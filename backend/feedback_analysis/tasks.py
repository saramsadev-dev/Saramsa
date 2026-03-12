
"""
Celery tasks for feedback analysis.
"""

import logging
import uuid
import os
from datetime import datetime, timezone
from celery import shared_task

from .services.ingestion_schedule_service import get_ingestion_schedule_service

logger = logging.getLogger(__name__)


@shared_task(name="feedback_analysis.run_scheduled_ingestions")
def run_scheduled_ingestions():
    service = get_ingestion_schedule_service()
    results = service.run_due_schedules()
    logger.info(
        "Scheduled ingestion run completed: due=%s started=%s skipped=%s",
        results.get("due"),
        results.get("started"),
        results.get("skipped"),
    )
    return results


# ---------------------------------------------------------------------------
# Slack sync tasks  (SAR-42)
# ---------------------------------------------------------------------------

@shared_task(name="sync_slack_sources")
def sync_slack_sources():
    """Periodic task: fetch new messages from ALL active Slack sources."""
    from integrations.services.slack_service import get_slack_service
    from integrations.services.source_service import get_source_service
    from .repositories import AnalysisRepository

    source_service = get_source_service()
    slack_service = get_slack_service()
    analysis_repo = AnalysisRepository()

    sources = source_service.get_active_sources_by_provider("slack")
    total_messages = 0
    sources_synced = 0
    errors = []

    for source in sources:
        try:
            count = _sync_one_source(source, slack_service, source_service, analysis_repo)
            total_messages += count
            sources_synced += 1
        except Exception as e:
            logger.error(f"Error syncing source {source.get('id')}: {e}", exc_info=True)
            errors.append({"source_id": source.get("id"), "error": str(e)})

    logger.info(
        "sync_slack_sources done: sources=%d messages=%d errors=%d",
        sources_synced, total_messages, len(errors),
    )
    return {
        "sources_synced": sources_synced,
        "total_messages": total_messages,
        "errors": errors,
    }


@shared_task(name="sync_single_slack_source")
def sync_single_slack_source(source_id: str, user_id: str):
    """On-demand sync for a single source (Sync Now button)."""
    from integrations.services.slack_service import get_slack_service
    from integrations.services.source_service import get_source_service
    from .repositories import AnalysisRepository

    source_service = get_source_service()
    slack_service = get_slack_service()
    analysis_repo = AnalysisRepository()

    source = source_service.get_source(source_id, user_id)
    if not source:
        logger.error(f"Source {source_id} not found for user {user_id}")
        return {"error": "source_not_found"}

    count = _sync_one_source(source, slack_service, source_service, analysis_repo)
    return {"source_id": source_id, "messages_synced": count}


# ---------------------------------------------------------------------------
# Shared helper
# ---------------------------------------------------------------------------

def _sync_one_source(source, slack_service, source_service, analysis_repo):
    """Sync a single Slack feedback source. Returns number of new messages stored."""
    source_id = source["id"]
    user_id = source["userId"]
    project_id = source["projectId"]
    account_id = source["accountId"]
    config = source.get("config", {})
    channels = config.get("channels", [])
    oldest = config.get("last_sync_cursor")

    # Collect existing source_ids for dedup
    existing_ids = _get_existing_source_ids(analysis_repo, project_id)

    total_new = 0
    latest_ts = oldest
    analysis_comments = []
    channel_names = []
    last_analyzed_ts = config.get("last_analyzed_ts")
    last_analyzed_at = config.get("last_analyzed_at")
    last_analysis_enqueued_at = config.get("last_analysis_enqueued_at")
    cooldown_seconds = int(os.getenv("SLACK_AUTO_ANALYSIS_COOLDOWN_SECONDS", "3600"))
    min_interval_seconds = int(os.getenv("SLACK_AUTO_ANALYSIS_MIN_INTERVAL_SECONDS", "1800"))

    for ch in channels:
        channel_id = ch.get("id", "")
        channel_name = ch.get("name", channel_id)

        raw_messages = slack_service.fetch_channel_messages(
            user_id, account_id, channel_id, oldest=oldest,
        )

        # Deduplicate
        new_messages = slack_service.deduplicate_messages(raw_messages, existing_ids)
        if not new_messages:
            continue

        # Resolve user names
        token = slack_service._get_bot_token(user_id, account_id)
        user_ids = list({m["user_id"] for m in new_messages if m.get("user_id")})
        user_names = slack_service.resolve_user_names(user_ids, token)

        # Normalize
        feedback_items = slack_service.normalize_to_feedback(
            new_messages, channel_name, user_names
        )

        # Store feedback as analysis comments linked to the project
        if feedback_items:
            _store_feedback(analysis_repo, project_id, user_id, feedback_items)
            total_new += len(feedback_items)
            for m in new_messages:
                text = m.get("text")
                ts = m.get("slack_ts")
                if text and ts:
                    analysis_comments.append({"ts": ts, "text": text})
            channel_names.append(channel_name)

            # Track latest timestamp for cursor
            for m in new_messages:
                if latest_ts is None or m["slack_ts"] > latest_ts:
                    latest_ts = m["slack_ts"]

            # Add to existing set so cross-channel dedup works within same run
            for m in new_messages:
                existing_ids.add(f"{m['channel_id']}_{m['slack_ts']}")

        logger.info(
            "Synced %d messages from #%s for project %s",
            len(feedback_items), channel_name, project_id,
        )

    # Update cursor
    now_iso = datetime.now(timezone.utc).isoformat()
    source_service.update_sync_cursor(source_id, user_id, latest_ts, now_iso)

    # Auto-analyze newly synced Slack comments (create analysis run)
    if analysis_comments:
        try:
            from .services.task_service import process_feedback_task
            cutoff_ts = None
            if last_analyzed_ts:
                try:
                    cutoff_ts = float(last_analyzed_ts)
                except Exception:
                    cutoff_ts = None
            elif last_analyzed_at:
                try:
                    cutoff_ts = datetime.fromisoformat(str(last_analyzed_at).replace("Z", "+00:00")).timestamp()
                except Exception:
                    cutoff_ts = None

            new_for_analysis = []
            for item in analysis_comments:
                try:
                    ts_val = float(item["ts"])
                except Exception:
                    continue
                if cutoff_ts is None or ts_val > cutoff_ts:
                    new_for_analysis.append(item)

            # Cooldown guard
            if last_analyzed_at:
                try:
                    last_dt = datetime.fromisoformat(str(last_analyzed_at).replace("Z", "+00:00"))
                    if (datetime.now(timezone.utc) - last_dt).total_seconds() < cooldown_seconds:
                        new_for_analysis = []
                except Exception:
                    pass
            # Enqueue throttle guard
            if last_analysis_enqueued_at:
                try:
                    enqueued_dt = datetime.fromisoformat(str(last_analysis_enqueued_at).replace("Z", "+00:00"))
                    if (datetime.now(timezone.utc) - enqueued_dt).total_seconds() < min_interval_seconds:
                        new_for_analysis = []
                except Exception:
                    pass

            if new_for_analysis:
                analysis_id = uuid.uuid4().hex
                unique_channels = sorted({c for c in channel_names if c})
                channel_label = ", ".join(unique_channels[:3])
                if len(unique_channels) > 3:
                    channel_label += f" +{len(unique_channels) - 3}"
                comments_only = [c["text"] for c in new_for_analysis]
                latest_new_ts = max(float(c["ts"]) for c in new_for_analysis)
                enqueued_at = datetime.now(timezone.utc).isoformat()
                source_service.update_analysis_status(
                    source_id,
                    user_id,
                    "queued",
                    error=None,
                    enqueued_at=enqueued_at,
                )
                process_feedback_task.delay(
                    comments_only,
                    None,
                    user_id,
                    project_id,
                    analysis_id,
                    None,
                )
        except Exception as e:
            logger.error(f"Error triggering Slack analysis: {e}", exc_info=True)

    return total_new


def _get_existing_source_ids(analysis_repo, project_id):
    """Query existing source_ids for a project where source=slack."""
    try:
        from integrations.models import SlackFeedbackItem
        return set(
            SlackFeedbackItem.objects.filter(
                project_id=project_id,
            ).values_list("source_id", flat=True)
        )
    except Exception:
        return set()


def _store_feedback(analysis_repo, project_id, user_id, feedback_items):
    """Persist normalised feedback items into the database."""
    import uuid
    from integrations.models import SlackFeedbackItem

    for item in feedback_items:
        try:
            SlackFeedbackItem.objects.create(
                id=f"sf_{uuid.uuid4().hex[:10]}",
                project_id=project_id,
                user_id=user_id,
                source_id=item["source_id"],
                comment=item["comment"],
                source_channel=item["source_channel"],
                author=item["author"],
                feedback_created_at=item["created_at"],
            )
        except Exception as e:
            logger.warning(f"Failed to store feedback item: {e}")


@shared_task(name="unsnooze_expired_candidates")
def unsnooze_expired_candidates():
    """Auto-resurface snoozed candidates when their snooze period expires."""
    from work_items.services import get_review_service
    review_service = get_review_service()
    count = review_service.unsnooze_expired()
    logger.info("Unsnoozed %d candidates", count)
    return count
