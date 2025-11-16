// Loading spinner component


interface LoadingSpinnerProps {
  message?: string;
}

export function LoadingSpinner({ message = 'Loading files...' }: LoadingSpinnerProps) {
  return (
    <div className="flex justify-center items-center p-4">
      <span className="loading loading-spinner loading-md text-blue-600"></span>
      <span className="ml-2 text-sm text-gray-600">{message}</span>
    </div>
  );
}
