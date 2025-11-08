import TaskList from '../components/TaskList';

export default function Tasks() {
  return (
    <div className="max-w-4xl mx-auto">
      <h2 className="text-2xl font-semibold mb-4 text-gray-800">Today's Tasks</h2>
      <p className="text-gray-600 mb-6">
        Here are your scheduled tasks for today. Mark them done as you complete them.
      </p>
      <TaskList />
    </div>
  );
}
