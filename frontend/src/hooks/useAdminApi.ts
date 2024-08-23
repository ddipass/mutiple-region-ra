import {
  ListBotApisRequest,
  ListBotApisResponse,
  ListPublicBotsRequest,
  ListPublicBotsResponse,
} from '../@types/api-publication';
import { GetPublicBotResponse } from '../@types/bot';
import useHttp from './useHttp';
import { 
  ListUsersRequest,
  ListUsersResponse,
} from '../@types/user';

const useAdminApi = () => {
  const http = useHttp();

  return {
    listBotApis: (req: ListBotApisRequest) => {
      return http.get<ListBotApisResponse>(['/admin/published-bots', req]);
    },
    listPublicBots: (req: ListPublicBotsRequest) => {
      return http.get<ListPublicBotsResponse>(
        !!req.start === !!req.end ? ['/admin/public-bots', req] : null
      );
    },
    listUsers: (req: ListUsersRequest) => {
      return http.get<ListUsersResponse>(
        !!req.start === !!req.end ? ['/admin/users', req] : null
      );
    },
    getPublicBot: (botId: string) => {
      return http.get<GetPublicBotResponse>(`/admin/bot/public/${botId}`);
    },
  };
};

export default useAdminApi;





