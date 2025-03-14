import { Auth } from 'aws-amplify';
import { useEffect, useState } from 'react';
import useSWR from 'swr';

const GROUP_PUBLISH_ALLOWED = 'PublishAllowed';
const GROUP_CREATING_BOT_ALLOWED = 'CreatingBotAllowed';
const GROUP_ADMIN = 'Admin';

const useUser = () => {
  const [isAllowApiSettings, setIsAllowApiSettings] = useState(false);
  const [isAllowCreatingBot, setIsAllowCreatingBot] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);

  const { data: session } = useSWR('current-session', () =>
    Auth.currentSession()
  );

  useEffect(() => {
    const groups: string[] | undefined =
      session?.getIdToken().payload['cognito:groups'];

    if (groups) {
      setIsAllowApiSettings(groups.some(group =>
        group === GROUP_PUBLISH_ALLOWED || group === GROUP_ADMIN
      ));
      setIsAllowCreatingBot(groups.some(group =>
        group === GROUP_CREATING_BOT_ALLOWED || group === GROUP_ADMIN
      ));
      setIsAdmin(groups.some(group =>
        group === GROUP_ADMIN
      ));
    } else {
      setIsAllowApiSettings(false);
      setIsAllowCreatingBot(false);
      setIsAdmin(false);
    }
  }, [session]);

  return {
    isAllowApiSettings,
    isAllowCreatingBot,
    isAdmin,
  };
};

export default useUser;