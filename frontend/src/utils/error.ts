type ApiErrorLike = {
  response?: {
    data?: {
      error?: string;
      message?: string;
      [key: string]: unknown;
    };
  };
  message?: string;
};

export const getErrorMessage = (
  error: unknown,
  fallback: string = 'Unexpected error occurred.',
): string => {
  if (typeof error === 'object' && error !== null) {
    const apiError = error as ApiErrorLike;
    return (
      apiError.response?.data?.error ??
      apiError.response?.data?.message ??
      apiError.message ??
      fallback
    );
  }
  return fallback;
};
