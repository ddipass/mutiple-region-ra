import React, { ReactNode, cloneElement, ReactElement } from 'react';
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
                  errorMessage={validationErrors.usagerules as string}
                  hasError={!!validationErrors.usagerules}
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
                  errorMessage={validationErrors.acknowledgement as string}
                  hasError={!!validationErrors.acknowledgement}
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
        async validateCustomSignIn(formData) {
          if (!formData.usagerules) {
            return {
              usagerules: t('auth.errors.mustAgreeUsageRules'),
            };
          }
        },
        async validateCustomSignUp(formData) {
          if (!formData.acknowledgement) {
            return {
              acknowledgement: t('auth.errors.mustAgreeTerms'),
            };
          }
        },
      }}>
      <>{cloneElement(children as ReactElement, { signOut })}</>
    </Authenticator>
  );
};

export default AuthAmplify;