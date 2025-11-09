import { useState } from 'react';

export default function TaskList() {
  const [tasks, setTasks] = useState([
    { id: 1, text: 'Reply to urgent emails', done: false, priority: 'high' },
    { id: 2, text: 'Finish report for team meeting', done: false, priority: 'medium' },
    { id: 3, text: 'Workout for 30 minutes', done: false, priority: 'low' },
  ]);

  const toggleTask = (id) => {
    setTasks(prev =>
      prev.map(task =>
        task.id === id ? { ...task, done: !task.done } : task
      )
    );
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high':
        return 'bg-red-100 text-red-800 border-red-300';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'low':
        return 'bg-green-100 text-green-800 border-green-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const completedCount = tasks.filter(t => t.done).length;
  const totalCount = tasks.length;

  return (
    <div className="space-y-4">
      {/* Progress Summary */}
      <div className="bg-white border-2 border-gray-200 rounded-2xl p-6 shadow-md">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-gray-800">Progress</h3>
          <span className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
            {completedCount}/{totalCount}
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
          <div
            className="bg-gradient-to-r from-blue-600 to-indigo-600 h-full rounded-full transition-all duration-500 ease-out"
            style={{ width: `${(completedCount / totalCount) * 100}%` }}
          ></div>
        </div>
        <p className="text-sm text-gray-600 mt-2">
          {completedCount === totalCount
            ? '🎉 All tasks completed! Great job!'
            : `${totalCount - completedCount} task${totalCount - completedCount !== 1 ? 's' : ''} remaining`}
        </p>
      </div>

      {/* Task List */}
      <ul className="space-y-3">
        {tasks.map((task, index) => (
          <li
            key={task.id}
            className={`group flex items-center gap-4 p-5 border-2 rounded-xl shadow-sm transition-all duration-200 hover:shadow-md hover:scale-[1.02] animate-slideUp ${
              task.done
                ? 'bg-gradient-to-br from-green-50 to-emerald-50 border-green-300'
                : 'bg-white border-gray-200 hover:border-blue-300'
            }`}
            style={{ animationDelay: `${index * 0.1}s` }}
          >
            {/* Custom Checkbox */}
            <label className="relative flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={task.done}
                onChange={() => toggleTask(task.id)}
                className="sr-only peer"
              />
              <div
                className={`w-6 h-6 border-2 rounded-lg transition-all duration-200 flex items-center justify-center ${
                  task.done
                    ? 'bg-gradient-to-br from-green-500 to-green-600 border-green-600'
                    : 'bg-white border-gray-300 group-hover:border-blue-400'
                }`}
              >
                {task.done && (
                  <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M5 13l4 4L19 7"/>
                  </svg>
                )}
              </div>
            </label>

            {/* Task Text */}
            <span
              className={`flex-1 text-lg transition-all duration-200 ${
                task.done
                  ? 'line-through text-gray-500'
                  : 'text-gray-800 font-medium'
              }`}
            >
              {task.text}
            </span>

            {/* Priority Badge */}
            <span
              className={`px-3 py-1 text-xs font-semibold rounded-full border ${getPriorityColor(
                task.priority
              )}`}
            >
              {task.priority.charAt(0).toUpperCase() + task.priority.slice(1)}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
