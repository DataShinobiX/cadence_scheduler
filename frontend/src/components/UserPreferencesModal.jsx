import { useEffect, useMemo, useState } from 'react';

const DEFAULT_PREFERENCES = {
  lunch_time: '12:00',
  break_duration: 15,
  work_hours_end: '17:00',
  work_hours_start: '09:00',
  gym_preferred_time: 'evening',
  focus_time_preference: 'morning',
  preferred_meeting_duration: 30
};

const PREFERENCE_FIELDS = [
  {
    key: 'work_hours_start',
    label: 'Work Day Start',
    type: 'time',
    helper: 'Tasks and meetings before this are avoided.'
  },
  {
    key: 'work_hours_end',
    label: 'Work Day End',
    type: 'time',
    helper: 'Helps keep evenings free unless urgent.'
  },
  {
    key: 'lunch_time',
    label: 'Lunch Time',
    type: 'time',
    helper: 'Blocks this slot to maintain a real break.'
  },
  {
    key: 'break_duration',
    label: 'Break Duration (minutes)',
    type: 'number',
    min: 5,
    max: 60,
    step: 5,
    helper: 'Used when scheduling quick reset breaks.'
  },
  {
    key: 'preferred_meeting_duration',
    label: 'Preferred Meeting Length (minutes)',
    type: 'number',
    min: 15,
    max: 120,
    step: 5,
    helper: 'Default length when booking meetings.'
  },
  {
    key: 'focus_time_preference',
    label: 'Focus Time Preference',
    type: 'select',
    options: ['morning', 'afternoon', 'evening'],
    helper: 'Determines when deep work blocks show up.'
  },
  {
    key: 'gym_preferred_time',
    label: 'Gym / Wellness Time',
    type: 'select',
    options: ['morning', 'afternoon', 'evening'],
    helper: 'Makes sure workouts land when you have energy.'
  }
];

const NUMBER_FIELDS = new Set(['break_duration', 'preferred_meeting_duration']);

export default function UserPreferencesModal({
  isOpen,
  onClose,
  preferences = {},
  loading = false,
  saving = false,
  onSubmit
}) {
  const [formValues, setFormValues] = useState(DEFAULT_PREFERENCES);

  useEffect(() => {
    if (isOpen) {
      setFormValues({
        ...DEFAULT_PREFERENCES,
        ...(preferences || {})
      });
    }
  }, [isOpen, preferences]);

  const handleChange = (key, value) => {
    setFormValues((prev) => ({
      ...prev,
      [key]: NUMBER_FIELDS.has(key) ? Number(value) : value
    }));
  };

  const displayValues = useMemo(
    () => ({
      ...DEFAULT_PREFERENCES,
      ...(preferences || {})
    }),
    [preferences]
  );

  const handleSubmit = (event) => {
    event.preventDefault();
    onSubmit?.(formValues);
  };

  if (!isOpen) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center px-4">
      <div className="absolute inset-0 bg-slate-900/60" onClick={saving ? undefined : onClose}></div>
      <div className="relative z-10 w-full max-w-lg rounded-2xl bg-white shadow-2xl">
        <div className="max-h-[calc(100vh-4rem)] overflow-y-auto p-6">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">Learned User Preferences</h2>
              <p className="mt-1 text-sm text-gray-500">
                These are the habits your assistant has learned. Tweak any field to retrain it instantly.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={saving}
            className="rounded-full bg-gray-100 p-2 text-gray-500 transition hover:bg-gray-200 hover:text-gray-700 disabled:cursor-not-allowed disabled:opacity-60"
            aria-label="Close preferences modal"
          >
            <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="mt-6 rounded-2xl bg-gradient-to-r from-blue-50 via-indigo-50 to-purple-50 p-4 text-sm text-blue-900">
          <p className="font-medium">Why this matters</p>
          <p className="text-blue-800">
            Meeting times, focus blocks, and reminders are tailored to these values. Share your true routine so the plan
            always feels personal.
          </p>
        </div>

          {loading ? (
            <div className="mt-10 flex flex-col items-center justify-center gap-3 py-8 text-gray-600">
              <div className="h-10 w-10 animate-spin rounded-full border-2 border-blue-200 border-t-blue-600" />
              <p>Fetching the latest preferences…</p>
            </div>
          ) : (
            <form className="mt-6 space-y-5" onSubmit={handleSubmit}>
              {PREFERENCE_FIELDS.map((field) => (
                <label key={field.key} className="block rounded-2xl border border-gray-100 p-4 shadow-sm">
                  <div className="flex items-center justify-between gap-4">
                    <div>
                      <p className="text-sm font-medium text-gray-900">{field.label}</p>
                      <p className="text-xs text-gray-500">{field.helper}</p>
                      <p className="mt-1 text-xs font-semibold text-blue-700">
                        Learned value: {displayValues[field.key]}
                      </p>
                    </div>
                    <div className="w-40">
                      {field.type === 'select' ? (
                        <select
                          className="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm font-medium text-gray-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                          value={formValues[field.key]}
                          onChange={(event) => handleChange(field.key, event.target.value)}
                          disabled={saving}
                          required
                        >
                          {field.options.map((option) => (
                            <option key={option} value={option}>
                              {option.charAt(0).toUpperCase() + option.slice(1)}
                            </option>
                          ))}
                        </select>
                      ) : (
                        <input
                          type={field.type}
                          min={field.min}
                          max={field.max}
                          step={field.step}
                          value={formValues[field.key]}
                          onChange={(event) => handleChange(field.key, event.target.value)}
                          disabled={saving}
                          required
                          className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm font-medium text-gray-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                        />
                      )}
                    </div>
                  </div>
                </label>
              ))}

              <p className="text-xs text-gray-500">
                Tip: Even changing a single value reshapes how your assistant drafts schedules, so be honest about your
                real habits.
              </p>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={onClose}
                  disabled={saving}
                  className="rounded-lg border border-gray-200 px-4 py-2 text-sm font-medium text-gray-600 transition hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="rounded-lg bg-gradient-to-r from-blue-600 to-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-blue-200 transition hover:from-blue-700 hover:to-indigo-700 disabled:cursor-not-allowed disabled:opacity-70"
                >
                  {saving ? 'Saving…' : 'Save Changes'}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
