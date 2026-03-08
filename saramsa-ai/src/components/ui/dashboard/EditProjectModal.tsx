'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Save } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Select } from '@/components/ui/select';
import type { Project } from '@/store/features/projects/projectsSlice';
import { apiRequest } from '@/lib/apiRequest';

interface EditProjectModalProps {
  project: Project;
  onClose: () => void;
  onSave: (projectId: string, name: string, description?: string) => Promise<void>;
  loading?: boolean;
}

export function EditProjectModal({ project, onClose, onSave, loading = false }: EditProjectModalProps) {
  const [name, setName] = useState(project.name);
  const [description, setDescription] = useState(project.description || '');
  const [scheduleLoading, setScheduleLoading] = useState(true);
  const [scheduleSaving, setScheduleSaving] = useState(false);
  const [scheduleError, setScheduleError] = useState<string | null>(null);
  const [cadence, setCadence] = useState<'off' | 'daily' | 'weekly'>('off');
  const [hourUtc, setHourUtc] = useState(2);
  const [dayOfWeek, setDayOfWeek] = useState(0);
  const [lastRunAt, setLastRunAt] = useState<string | null>(null);
  const [lastRunSuccess, setLastRunSuccess] = useState<boolean | null>(null);
  const [nextRunAt, setNextRunAt] = useState<string | null>(null);
  const maxDescriptionLength = 100;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (name.trim()) {
      setScheduleError(null);
      try {
        setScheduleSaving(true);
        await onSave(project.id, name.trim(), description.trim() || undefined);
        await saveSchedule();
        onClose();
      } catch (error: any) {
        const message = error?.message || 'Failed to save project settings.';
        setScheduleError(message);
      } finally {
        setScheduleSaving(false);
      }
    }
  };

  const formatDateTime = (value: string | null) => {
    if (!value) return '—';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return '—';
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit'
    });
  };

  const loadSchedule = async () => {
    setScheduleLoading(true);
    setScheduleError(null);
    try {
      const response = await apiRequest('get', '/insights/ingestion/schedule/', {
        project_id: project.id
      }, true);
      const schedule = response.data?.data?.schedule || null;
      if (!schedule) {
        setCadence('off');
        setHourUtc(2);
        setDayOfWeek(0);
        setLastRunAt(null);
        setLastRunSuccess(null);
        setNextRunAt(null);
        return;
      }
      const enabled = Boolean(schedule.enabled);
      setCadence(enabled ? schedule.cadence || 'daily' : 'off');
      setHourUtc(typeof schedule.hour_utc === 'number' ? schedule.hour_utc : 2);
      setDayOfWeek(typeof schedule.day_of_week === 'number' ? schedule.day_of_week : 0);
      setLastRunAt(schedule.last_run_at || null);
      setLastRunSuccess(typeof schedule.last_run_success === 'boolean' ? schedule.last_run_success : null);
      setNextRunAt(schedule.next_run_at || null);
    } catch (error: any) {
      setScheduleError(error?.message || 'Failed to load schedule.');
    } finally {
      setScheduleLoading(false);
    }
  };

  const saveSchedule = async () => {
    const enabled = cadence !== 'off';
    const payload = {
      enabled,
      cadence: cadence === 'off' ? 'daily' : cadence,
      hour_utc: hourUtc,
      day_of_week: cadence === 'weekly' ? dayOfWeek : null
    };
    const response = await apiRequest('post', '/insights/ingestion/schedule/', {
      project_id: project.id,
      schedule: payload
    }, true);
    const schedule = response.data?.data?.schedule || null;
    if (schedule) {
      setLastRunAt(schedule.last_run_at || null);
      setLastRunSuccess(typeof schedule.last_run_success === 'boolean' ? schedule.last_run_success : null);
      setNextRunAt(schedule.next_run_at || null);
    }
  };

  useEffect(() => {
    loadSchedule();
  }, [project.id]);

  const isSaving = loading || scheduleSaving;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          className="bg-card/95 rounded-xl shadow-xl max-w-md w-full"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-border/60">
            <h2 className="text-xl font-semibold text-foreground">
              Edit Project
            </h2>
            <Button
              onClick={onClose}
              variant="ghost"
              size="icon"
              className="h-8 w-8 hover:bg-accent/60"
              disabled={loading}
            >
              <X className="w-5 h-5 text-muted-foreground" />
            </Button>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="p-6 space-y-4">
            <div>
              <label htmlFor="project-name" className="block text-sm font-medium text-muted-foreground mb-2">
                Project Name *
              </label>
              <Input
                id="project-name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full px-3 py-2 border border-border/60 rounded-xl bg-background/80 text-foreground focus:ring-2 focus:ring-saramsa-brand/30 focus:border-saramsa-brand/40"
                placeholder="Enter project name"
                required
                disabled={isSaving}
              />
            </div>

            <div>
              <label htmlFor="project-description" className="block text-sm font-medium text-muted-foreground mb-2">
                Description
              </label>
              <Textarea
                id="project-description"
                value={description}
                onChange={(e) => {
                  const value = e.target.value;
                  if (value.length <= maxDescriptionLength) {
                    setDescription(value);
                  }
                }}
                rows={3}
                className="w-full px-3 py-2 border border-border/60 rounded-xl bg-background/80 text-foreground focus:ring-2 focus:ring-saramsa-brand/30 focus:border-saramsa-brand/40 resize-none"
                placeholder="Enter project description (optional)"
                disabled={isSaving}
              />
              <div className="flex justify-end items-center mt-1">
                <p className="text-xs text-muted-foreground">
                  {description.length}/{maxDescriptionLength}
                </p>
              </div>
            </div>

            <div className="rounded-xl border border-border/60 bg-background/60 p-4 space-y-3">
              <div>
                <h3 className="text-sm font-semibold text-foreground">Scheduled Ingestion</h3>
                <p className="text-xs text-muted-foreground">
                  Auto-run analysis on a daily or weekly cadence (UTC time).
                </p>
              </div>

              {scheduleLoading ? (
                <p className="text-xs text-muted-foreground">Loading schedule…</p>
              ) : (
                <>
                  <div className="grid grid-cols-1 gap-3">
                    <div>
                      <label className="block text-xs font-medium text-muted-foreground mb-2">
                        Frequency
                      </label>
                      <Select
                        value={cadence}
                        onChange={(e) => setCadence(e.target.value as 'off' | 'daily' | 'weekly')}
                        disabled={isSaving}
                      >
                        <option value="off">Off</option>
                        <option value="daily">Daily</option>
                        <option value="weekly">Weekly</option>
                      </Select>
                    </div>

                    <div>
                      <label className="block text-xs font-medium text-muted-foreground mb-2">
                        Time (UTC)
                      </label>
                      <Select
                        value={String(hourUtc)}
                        onChange={(e) => setHourUtc(Number(e.target.value))}
                        disabled={isSaving || cadence === 'off'}
                      >
                        {Array.from({ length: 24 }).map((_, hour) => (
                          <option key={hour} value={hour}>{`${hour.toString().padStart(2, '0')}:00`}</option>
                        ))}
                      </Select>
                    </div>

                    {cadence === 'weekly' && (
                      <div>
                        <label className="block text-xs font-medium text-muted-foreground mb-2">
                          Day of Week (UTC)
                        </label>
                        <Select
                          value={String(dayOfWeek)}
                          onChange={(e) => setDayOfWeek(Number(e.target.value))}
                          disabled={isSaving}
                        >
                          <option value="0">Monday</option>
                          <option value="1">Tuesday</option>
                          <option value="2">Wednesday</option>
                          <option value="3">Thursday</option>
                          <option value="4">Friday</option>
                          <option value="5">Saturday</option>
                          <option value="6">Sunday</option>
                        </Select>
                      </div>
                    )}
                  </div>

                  <div className="rounded-lg bg-secondary/40 px-3 py-2 text-xs text-muted-foreground space-y-1">
                    <div className="flex items-center justify-between">
                      <span>Last run</span>
                      <span className="text-foreground">{formatDateTime(lastRunAt)}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>Status</span>
                      <span className="text-foreground">
                        {lastRunSuccess === null ? '—' : lastRunSuccess ? 'Success' : 'Failed'}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>Next run</span>
                      <span className="text-foreground">{formatDateTime(nextRunAt)}</span>
                    </div>
                  </div>
                </>
              )}
            </div>

            {scheduleError && (
              <div className="rounded-xl border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20 px-3 py-2 text-xs text-red-700 dark:text-red-300">
                {scheduleError}
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-3 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={onClose}
                className="flex-1"
                disabled={isSaving}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="saramsa"
                className="flex-1 gap-2"
                disabled={isSaving || !name.trim()}
              >
                <Save className="w-4 h-4" />
                {isSaving ? 'Saving...' : 'Save Changes'}
              </Button>
            </div>
          </form>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}


