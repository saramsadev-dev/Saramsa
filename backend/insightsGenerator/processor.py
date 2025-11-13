import asyncio
import os
import sys
import uuid
import json
from collections import defaultdict
from datetime import datetime
from aiCore.chunker import process_chunks
from aiCore.cosmos_service import cosmos_service

from .prompts import getSentAnalysisPrompt, getDeepAnalysisPrompt

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def process_feedback(text):
    prompt = getSentAnalysisPrompt()
    commentsAnalysis = await process_chunks(text, prompt, 0)
    print("commentAnalysis", commentsAnalysis)

    prompt = getDeepAnalysisPrompt()
    deepAnalysis = await process_chunks(text, prompt, 1)
    print("deepAnalysis", deepAnalysis)

    # Ensure lists
    if isinstance(commentsAnalysis, str):
        commentsAnalysis = [commentsAnalysis]
    if isinstance(deepAnalysis, str):
        deepAnalysis = [deepAnalysis]

    # --- Normalize comment analysis across chunks ---
    total_count = 0
    total_pos = 0
    total_neg = 0
    total_neu = 0

    feature_map = {}
    # keywords aggregation by polarity
    pos_kw_scores = defaultdict(float)
    pos_kw_counts = defaultdict(int)
    neg_kw_scores = defaultdict(float)
    neg_kw_counts = defaultdict(int)

    def safe_parse(item):
        if isinstance(item, dict):
            return item
        try:
            return json.loads(item)
        except Exception:
            return {}

    for item in commentsAnalysis:
        data = safe_parse(item)
        counts = data.get('counts') or {}
        # counts may contain absolute numbers
        t_total = counts.get('total') or 0
        # Accept either absolute counts or percentages under sentimentsummary/sentiment_summary
        sentiments_any = data.get('sentimentsummary') or data.get('sentiment_summary') or {}
        t_pos = counts.get('positive') or 0
        t_neg = counts.get('negative') or 0
        t_neu = counts.get('neutral') or 0
        # If counts are missing but sentiments present and a total exists, estimate absolute numbers
        if t_total and (not t_pos and not t_neg and not t_neu) and sentiments_any:
            try:
                p = float(sentiments_any.get('positive') or 0) / 100.0
                n = float(sentiments_any.get('negative') or 0) / 100.0
                z = float(sentiments_any.get('neutral') or 0) / 100.0
                t_pos = round(t_total * p)
                t_neg = round(t_total * n)
                t_neu = max(0, t_total - t_pos - t_neg)
            except Exception:
                pass
        total_count += t_total
        total_pos += t_pos
        total_neg += t_neg
        total_neu += t_neu

        # features list (feature_asba / featureasba)
        features_list = data.get('feature_asba') or data.get('featureasba') or []
        for feat in features_list:
            name = (feat.get('feature') or '').strip()
            if not name:
                continue
            key = name.lower()
            existing = feature_map.get(key)
            sentiment = feat.get('sentiment') or {}
            # Some models may emit description/sentiment/keywords in various casings
            description_value = (
                feat.get('description')
                or feat.get('feature_description')
                or feat.get('desc')
                or ''
            )
            keywords_value = feat.get('keywords') or feat.get('feature_keywords') or []
            # Prepare merged feature structure
            if not existing:
                feature_map[key] = {
                    'name': name,
                    'description': description_value,
                    'sentiment': {
                        'positive': float(sentiment.get('positive') or 0),
                        'negative': float(sentiment.get('negative') or 0),
                        'neutral': float(sentiment.get('neutral') or 0),
                    },
                    'keywords': list(keywords_value),
                    # Optional: count per feature if provided in future prompts
                }
            else:
                # Merge: average sentiment and union keywords; preserve first description if missing
                if not existing.get('description') and description_value:
                    existing['description'] = description_value
                # Average sentiments (simple mean across chunks)
                for k in ('positive', 'negative', 'neutral'):
                    try:
                        existing['sentiment'][k] = (
                            existing['sentiment'][k] + float(sentiment.get(k) or 0)
                        ) / 2.0
                    except Exception:
                        pass
                # Merge keywords
                kw_set = set(existing.get('keywords') or [])
                for kw in (keywords_value or []):
                    if kw not in kw_set:
                        existing['keywords'].append(kw)
                        kw_set.add(kw)

        # aggregate global positive/negative keywords for word cloud
        for kw in (data.get('positive_keywords') or data.get('positivekeywords') or []):
            word = kw.get('keyword') if isinstance(kw, dict) else None
            score = kw.get('sentiment') if isinstance(kw, dict) else None
            if word:
                pos_kw_counts[word] += 1
                if isinstance(score, (int, float)):
                    pos_kw_scores[word] += float(score)
        for kw in (data.get('negative_keywords') or data.get('negativekeywords') or []):
            word = kw.get('keyword') if isinstance(kw, dict) else None
            score = kw.get('sentiment') if isinstance(kw, dict) else None
            if word:
                neg_kw_counts[word] += 1
                if isinstance(score, (int, float)):
                    neg_kw_scores[word] += float(score)

    # Build overall sentiment percentages if we have totals
    overall = None
    if total_count > 0:
        overall = {
            'positive': round((total_pos / total_count) * 100, 2) if total_count else 0,
            'negative': round((total_neg / total_count) * 100, 2) if total_count else 0,
            'neutral': round((total_neu / total_count) * 100, 2) if total_count else 0,
        }

    # Consolidate features array
    normalized_features = list(feature_map.values())

    # Consolidate global keywords
    def consolidate_kw(scores, counts):
        items = []
        for w, c in counts.items():
            avg = scores[w] / c if c else 0.0
            items.append({'keyword': w, 'sentiment': round(avg, 3)})
        # Sort by count desc then sentiment desc
        items.sort(key=lambda x: (counts[x['keyword']], x['sentiment']), reverse=True)
        return items

    positive_keywords = consolidate_kw(pos_kw_scores, pos_kw_counts)
    negative_keywords = consolidate_kw(neg_kw_scores, neg_kw_counts)

    # Compose normalized commentAnalysis dictionary as requested
    normalized_comment_analysis = {
        'overall': overall,
        'counts': {
            'total': total_count,
            'positive': total_pos,
            'negative': total_neg,
            'neutral': total_neu,
        },
        'features': normalized_features,
        'positive_keywords': positive_keywords,
        'negative_keywords': negative_keywords,
    }

    # Save insights to Cosmos DB (normalized schema with raw LLM outputs preserved)
    try:
        insight_id = str(uuid.uuid4())
        insight_data = {
            'id': f'insight_{insight_id}',
            'type': 'insight',
            'analysis_type': 'feedback_analysis',
            'analysis_date': datetime.now().isoformat(),
            'schema_version': 2,
            'overall': overall,
            'counts': {
                'total': total_count,
                'positive': total_pos,
                'negative': total_neg,
                'neutral': total_neu,
            },
            'features': normalized_features,
            'positive_keywords': positive_keywords,
            'negative_keywords': negative_keywords,
            'commentAnalysis': normalized_comment_analysis,
            'raw_llm': {
                'comment_chunks': commentsAnalysis,
                'deep_chunks': deepAnalysis,
            },
            'metadata': {
                'source': 'file_upload',
                'text_length': len(text),
                'processing_timestamp': datetime.now().isoformat()
            }
        }
        
        saved_analysis = cosmos_service.save_analysis_data(insight_data)
        if saved_analysis:
            print(f"Analysis saved to Cosmos DB with ID: {saved_analysis.get('id')}")
    except Exception as e:
        print(f"Error saving insight to Cosmos DB: {e}")

    # Return normalized + raw for immediate use
    return {
        'overall': overall,
        'counts': {
            'total': total_count,
            'positive': total_pos,
            'negative': total_neg,
            'neutral': total_neu,
        },
        'features': normalized_features,
        'positive_keywords': positive_keywords,
        'negative_keywords': negative_keywords,
        'commentAnalysis': normalized_comment_analysis,
        'raw_llm': {
            'comment_chunks': commentsAnalysis,
            'deep_chunks': deepAnalysis,
        }
    }

async def process_uploaded_data_async(data, file_type, doc_type):
    if file_type == 'json':
        print("Processing JSON data:")

        if (doc_type == 0):
            # data = flatten_feedback(data)
            result = await process_feedback(str(data))
            return result
        
        # User Stories
        if (doc_type == 1):
            return {'status': 'success', 'details': 'Not implemented'}

    elif file_type == 'csv':
        print("Processing CSV data:", data)
        # Simulate async processing
        await asyncio.sleep(1)
        return {
            'status': 'success', 
            'details': 'CSV data processed asynchronously'
        }
    
    return {'status': 'error', 'details': 'Unknown file type'}
