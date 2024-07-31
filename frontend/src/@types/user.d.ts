export type ListUsersRequest = {
  limit?: number;
  start?: string;
  end?: string;
};

export type ListUsersResponse = {
  id: string;
  email: string;
  description: string;
  totalPrice: number;
  isAccurate: boolean;
}[];

