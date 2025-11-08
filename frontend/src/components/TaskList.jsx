import { useState } from 'react';

export default function TaskList() {
  const [tasks, setTasks] = useState([
    { id: 1, text: 'Reply to urgent emails', done: false },
    { id: 2, text: 'Finish report for team meeting', done: false },
    { id: 3, text: 'Workout for 30 minutes', done: false },
  ]);

  const toggleTask = (id) => {
    setTasks(prev =>
      prev.map(task =>
        task.id === id ? { ...task, done: !task.done } : task
      )
    );
  };

  return (
    <ul className="space-y-4">
      {tasks.map(task => (
        <li
          key={task.id}
          className={`flex items-center gap-3 p-4 border rounded-md ${
            task.done ? 'bg-green-50' : 'bg-white'
          }`}
        >
          <input
            type="checkbox"
            checked={task.done}
            onChange={() => toggleTask(task.id)}
            className="w-5 h-5"
          />
          <span
            className={`text-gray-800 ${
              task.done ? 'line-through text-gray-500' : ''
            }`}
          >
            {task.text}
          </span>
        </li>
      ))}
    </ul>
  );
}
