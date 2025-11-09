import TaskList from '../components/TaskList';

export default function Tasks() {
  return (
    <div className="max-w-4xl mx-auto animate-fadeIn">
      <div className="mb-6 text-center">
        <h2 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent mb-2">
          Today's Tasks
        </h2>
        <p className="text-gray-600 text-lg">
          Track your progress and stay organized
        </p>
      </div>
      <TaskList />
    </div>
  );
}
