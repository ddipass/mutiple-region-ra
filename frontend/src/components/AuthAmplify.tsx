import React, { ReactNode, cloneElement, ReactElement } from 'react';
import { BaseProps } from '../@types/common';
import { useTranslation } from 'react-i18next';
import { SocialProvider } from '../@types/auth';
import { 
  Authenticator, 
  useAuthenticator, 
  useTheme, 
  CheckboxField, 
  Heading
} from '@aws-amplify/ui-react';

const MISTRAL_ENABLED: boolean =
  import.meta.env.VITE_APP_ENABLE_MISTRAL === 'true';

type Props = BaseProps & {
  socialProviders: SocialProvider[];
  children: ReactNode;
};

const AuthAmplify: React.FC<Props> = ({ socialProviders, children }) => {
  const { t } = useTranslation();
  const { signOut } = useAuthenticator();

  const components = {
    Header() {
      return (
          <div className="mb-5 mt-10 flex justify-center text-3xl text-aws-font-color">
            {!MISTRAL_ENABLED ? t('app.name') : t('app.nameWithoutClaude')}
          </div>
      );
    },
    SignIn: {
      Header() {
        return <Heading>Sign In</Heading>;
      },
      Footer() {
        return (
          <CheckboxField
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
        );
      },
    },
    SignUp: {
      Header() {
        return <Heading>Sign Up</Heading>;
      },
      Footer() {
        return (
          <CheckboxField
            name="acknowledgement"
            value="yes"
            label={t('auth.agreeTerms')}
          />
        );
      },
    },
  };

  const services = {
    async validateCustomSignIn(formData: Record<string, any>) {
      if (!formData.usagerules) {
        return {
          usagerules: t('auth.errors.mustAgreeUsageRules'),
        };
      }
    },
    async validateCustomSignUp(formData: Record<string, any>) {
      if (!formData.acknowledgement) {
        return {
          acknowledgement: t('auth.errors.mustAgreeTerms'),
        };
      }
    },
  };

  const formFields = {
     signUp: {
       email: {
         order:1
       },
       family_name: {
         order: 2
       },
       preferred_username: {
         order: 4
       },
       birthdate: {
         order: 3
       },
       password: {
         order: 5
       },
       confirm_password: {
         order: 6
       }
     },
  };

  const signUpAttributes={['birthdate', 'family_name', 'preferred_username']};

  return (
    <Authenticator
      socialProviders={socialProviders}
      initialState="signUp"
      components={components}
      services={services}
      formFields={formFields} 
      signUpAttributes={signUpAttributes}
    >
      <>{cloneElement(children as ReactElement, { signOut })}</>
    </Authenticator>
  );
};

export default AuthAmplify;