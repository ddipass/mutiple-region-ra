import { ListUsersRequest } from '../@types/user';
import useAdminApi from './useAdminApi';

const useAdminUsers = (params: ListUsersRequest) => {
  const { listUsers } = useAdminApi();

  const { data, isLoading, mutate } = listUsers(params);

  return {
    adminUsers: data,
    isLoading,
    mutate,
  };
};

export default useAdminUsers;
