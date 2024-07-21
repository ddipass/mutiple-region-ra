import React, { ReactNode, cloneElement, ReactElement, useState } from 'react';
import { BaseProps } from '../@types/common';
import { useTranslation } from 'react-i18next';
import { SocialProvider } from '../@types/auth';
import { Authenticator } from '@aws-amplify/ui-react';
import { CheckboxField } from '@aws-amplify/ui-react';
import { useAuthenticator } from '@aws-amplify/ui-react';


const MISTRAL_ENABLED: boolean =
  import.meta.env.VITE_APP_ENABLE_MISTRAL === 'true';

type Props = BaseProps & {
  socialProviders: SocialProvider[];
  children: ReactNode;
};

const AuthAmplify: React.FC<Props> = ({ socialProviders, children }) => {
  const { t } = useTranslation();
  const { signOut } = useAuthenticator();

  const [signInError, setSignInError] = useState<string | null>(null);
  const [signUpError, setSignUpError] = useState<string | null>(null);

  const handleSignIn = (formData: Record<string, any>) => {
    if (!formData.usagerules) {
      setSignInError(t('auth.errors.mustAgreeUsageRules'));
      return;
    }
    setSignInError(null);
    // 这里可以添加正常的登录逻辑
  };

  const handleSignUp = (formData: Record<string, any>) => {
    if (!formData.acknowledgement) {
      setSignUpError(t('auth.errors.mustAgreeTerms'));
      return;
    }
    setSignUpError(null);
    // 这里可以添加正常的注册逻辑
  };

  return (
    <Authenticator
      socialProviders={socialProviders}
      initialState="signUp"
      components={{
        Header: () => (
          <div className="mb-5 mt-10 flex justify-center text-3xl text-aws-font-color">
            {!MISTRAL_ENABLED ? t('app.name') : t('app.nameWithoutClaude')}
          </div>
        ),
        SignIn: {
          FormFields() {
            const { validationErrors } = useAuthenticator();
            return (
              <>
                <Authenticator.SignIn.FormFields />
                <CheckboxField
                  errorMessage={signInError || (validationErrors.usagerules as string)}
                  hasError={!!signInError || !!validationErrors.usagerules}
                  name="usagerules"
                  value="yes"
                  label={
                    <>
                      {t('auth.agreeUsageRules')} 
                      <a href="/usage-rules" target="_blank" rel="noopener noreferrer">
                        {t('auth.viewRules')}
                      </a>
                    </>
                  }
                />
              </>
            );
          },
        },
        SignUp: {
          FormFields() {
            const { validationErrors } = useAuthenticator();
            return (
              <>
                <Authenticator.SignUp.FormFields />
                <CheckboxField
                  errorMessage={signUpError || (validationErrors.acknowledgement as string)}
                  hasError={!!signUpError || !!validationErrors.acknowledgement}
                  name="acknowledgement"
                  value="yes"
                  label={t('auth.agreeTerms')}
                />
              </>
            );
          },
        },
      }}
      services={{
        async handleSignIn(formData) {
          handleSignIn(formData);
          // 如果没有错误，返回 undefined 让 Amplify 继续处理
          return signInError ? { ...formData, error: signInError } : undefined;
        },
        async handleSignUp(formData) {
          handleSignUp(formData);
          // 如果没有错误，返回 undefined 让 Amplify 继续处理
          return signUpError ? { ...formData, error: signUpError } : undefined;
        },
      }}>
      <>{cloneElement(children as ReactElement, { signOut })}</>
    </Authenticator>
  );
};

export default AuthAmplify;