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

  const components = {
    Header() {
      return (
        <div className="mb-5 mt-10 flex justify-center text-2xl text-aws-font-color">
          {!MISTRAL_ENABLED ? t('app.name') : t('app.nameWithoutClaude')}
        </div>
      );
    },
    Footer() {
      const { tokens } = useTheme();
      return (
        <View textAlign="center" padding={tokens.space.large}>
          <Text color={tokens.colors.neutral[80]}>
            &copy; All Rights Reserved
          </Text>
        </View>
      );
    },
    SignUp: {
      FormFields() {
        const { tokens } = useTheme();
        return (
          <>
            {/* Re-use default `Authenticator.SignUp.FormFields` */}
            <Authenticator.SignUp.FormFields />

            {/* Append & require Terms and Conditions field to sign in  */}
            <ViewTermsButton />
            <Text color={tokens.colors.neutral[80]}>
              By create account of this research platform you must agree & follow "user agreement" & "usage rules". 
            </Text>
          </>
        );
      },
    },
  };

  // const formFields = {
  //    signUp: {
  //      email: {
  //        order:1
  //      },
  //      phone_number: {
  //        order:2,
  //        dialCode: ['+86']
  //      },
  //      password: {
  //        order: 3
  //      },
  //      confirm_password: {
  //        order: 4
  //      }
  //    },
  // };

  return (
    <Authenticator
      socialProviders={socialProviders}
      initialState="signIn"
      components={components}
      // formFields={formFields} 
    >
      <>{cloneElement(children as ReactElement, { signOut })}</>
    </Authenticator>
  );
};

export default AuthAmplify;
