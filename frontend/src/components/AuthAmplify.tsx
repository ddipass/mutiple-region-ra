import React, { ReactNode, cloneElement, ReactElement } from 'react';
import { BaseProps } from '../@types/common';
import { useTranslation } from 'react-i18next';
import { SocialProvider } from '../@types/auth';
import { 
  Authenticator, 
  useAuthenticator, 
  useTheme,
  View,
  Text,
  Button
} from '@aws-amplify/ui-react';


const MISTRAL_ENABLED: boolean =
  import.meta.env.VITE_APP_ENABLE_MISTRAL === 'true';

type Props = BaseProps & {
  socialProviders: SocialProvider[];
  children: ReactNode;
};

const ViewTermsButton = () => {
  const handleViewTerms = () => {
    window.open('/agreement', '_blank');
  };
  const handleUsageRules = () => {
    window.open('/usage-rules', '_blank');
  };
  const { t } = useTranslation();

  return (
    <div className="flex flex-row justify-center space-x-4">
      <Button onClick={handleViewTerms} variation="link">
        {t('auth.viewTerms')}
      </Button>
      <Button onClick={handleUsageRules} variation="link">
        {t('auth.viewRules')}
      </Button>
    </div>
  );
};

const AuthAmplify: React.FC<Props> = ({ socialProviders, children }) => {
  const { t } = useTranslation();
  const { signOut } = useAuthenticator();

  return (
    <Authenticator
      socialProviders={socialProviders}
      components={{
        Header: () => (
          <div className="mb-5 mt-10 flex justify-center text-3xl text-aws-font-color">
            {!MISTRAL_ENABLED ? t('app.name') : t('app.nameWithoutClaude')}
          </div>
        ),
        Footer() {
          const { tokens } = useTheme();
          return (
           <>
            <Text color={tokens.colors.neutral[80]} padding={tokens.space.large} textAlign="justify">
              By create account of this research platform you must agree & follow "user agreement" & "usage rules". 
            </Text>
            <ViewTermsButton />
            <Text color={tokens.colors.neutral[80]} padding={tokens.space.large} textAlign="justify">
              This platform has been developed and deployed for research purposes. Features and functionality may be updated periodically without prior notice. Please note that we do not offer any Service Level Agreement (SLA) for this platform.
            </Text>
            <View textAlign="center" padding={tokens.space.large}>
              <Text color={tokens.colors.neutral[80]}>
                Amazon Research &copy; All Rights Reserved. 
              </Text>
            </View>
           </>
          );
        },
      }}>
      <>{cloneElement(children as ReactElement, { signOut })}</>
    </Authenticator>
  );
};

export default AuthAmplify;
