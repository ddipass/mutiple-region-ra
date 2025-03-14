import App from './App.tsx';
import ChatPage from './pages/ChatPage.tsx';
import NotFound from './pages/NotFound.tsx';
import BotExplorePage from './pages/BotExplorePage.tsx';
import BotEditPage from './pages/BotEditPage.tsx';
import BotApiSettingsPage from './pages/BotApiSettingsPage.tsx';
import AdminSharedBotAnalyticsPage from './pages/AdminSharedBotAnalyticsPage.tsx';
import AdminApiManagementPage from './pages/AdminApiManagementPage.tsx';
import AdminBotManagementPage from './pages/AdminBotManagementPage.tsx';
import AdminUsersPage from './pages/AdminUsersPage.tsx';
import { useTranslation } from 'react-i18next';
import {
  createBrowserRouter,
  matchRoutes,
  RouteObject,
  useLocation,
} from 'react-router-dom';
import { useMemo } from 'react';
import UsageRules from './pages/UsageRules';
import UsrAgreement from './pages/UsrAgreement';

const rootChildren = [
  {
    path: '/',
    element: <ChatPage />,
  },
  {
    path: '/bot/explore',
    element: <BotExplorePage />,
  },
  {
    path: '/bot/new',
    element: <BotEditPage />,
  },
  {
    path: '/bot/edit/:botId',
    element: <BotEditPage />,
  },
  {
    path: '/bot/api-settings/:botId',
    element: <BotApiSettingsPage />,
  },
  {
    path: '/bot/:botId',
    element: <ChatPage />,
  },
  {
    path: '/admin/shared-bot-analytics',
    element: <AdminSharedBotAnalyticsPage />,
  },
  {
    path: '/admin/api-management',
    element: <AdminApiManagementPage />,
  },
  {
    path: '/admin/bot/:botId',
    element: <AdminBotManagementPage />,
  },
  {
    path: '/admin/users',
    element: <AdminUsersPage />,
  },
  {
    path: '/:conversationId',
    element: <ChatPage />,
  },
  {
    path: '*',
    element: <NotFound />,
  },
] as const;

const routes = [
  {
    path: '/usage-rules',
    element: <UsageRules />,
  },
  {
    path: '/agreement',
    element: <UsrAgreement />,
  },
  {
    path: '/',
    element: <App />,
    children: rootChildren,
  },
];

type AllPaths = (typeof rootChildren)[number]['path'] | '/usage-rules' | '/agreement';

const getAllPaths = (routes: typeof rootChildren): AllPaths[] =>
  routes.map(({ path }) => path);

export const allPaths = [...getAllPaths(rootChildren), '/usage-rules', '/agreement'];

export const usePageLabel = () => {
  const { t } = useTranslation();
  const pageLabel: { path: (typeof allPaths)[number]; label: string }[] = [
    { path: '/agreement', label: t('usrAgreement.pageTitle') }, // 添加 usrAgreement 的标签
    { path: '/usage-rules', label: t('usageRules.pageTitle') }, // 添加 UsageRules 的标签
    { path: '/bot/explore', label: t('bot.explore.label.pageTitle') },
    {
      path: '/admin/shared-bot-analytics',
      label: t('admin.sharedBotAnalytics.label.pageTitle'),
    },
    {
      path: '/admin/api-management',
      label: t('admin.apiManagement.label.pageTitle'),
    },
  ];

  const getPageLabel = (pagePath: (typeof allPaths)[number]) =>
    pageLabel.find(({ path }) => path === pagePath)?.label;
  return { pageLabel, getPageLabel };
};

// export const router = createBrowserRouter(routes as unknown as RouteObject[]);
export const router = createBrowserRouter(routes as RouteObject[]);

type ConversationRoutes = { path: (typeof allPaths)[number] }[];

export const usePageTitlePathPattern = () => {
  const location = useLocation();

  const conversationRoutes: ConversationRoutes = useMemo(
    () => [
      { path: '/:conversationId' },
      { path: '/bot/:botId' },
      { path: '/' },
      { path: '*' },
    ],
    []
  );
  const notConversationRoutes = useMemo(
    () =>
      allPaths
        .filter(
          (pattern) => !conversationRoutes.find(({ path }) => path === pattern)
        )
        .map((pattern) => ({ path: pattern })),
    [conversationRoutes]
  );
  const matchedRoutes = useMemo(() => {
    return matchRoutes(notConversationRoutes, location);
  }, [location, notConversationRoutes]);

  const pathPattern = useMemo(
    () => matchedRoutes?.[0]?.route.path ?? '/',
    [matchedRoutes]
  );

  const isConversationOrNewChat = useMemo(
    () => !matchedRoutes?.length,
    [matchedRoutes]
  );
  return { isConversationOrNewChat, pathPattern };
};
