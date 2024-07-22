import React, { ReactNode, cloneElement, ReactElement, useState } from 'react';
import { BaseProps } from '../@types/common';
import { useTranslation } from 'react-i18next';
import { SocialProvider } from '../@types/auth';
import { 
  Authenticator, 
  useAuthenticator, 
  CheckboxField,
  useTheme,
  View,
  Text
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
        const { validationErrors, updateFormData } = useAuthenticator();
        const [isChecked, setIsChecked] = useState(false);

        const handleCheckboxChange = (event) => {
          const newCheckedState = event.target.checked;
          setIsChecked(newCheckedState);
          updateFormData({
            acknowledgement: newCheckedState ? 'yes' : '',
          });
        };

        return (
          <>
            <Authenticator.SignUp.FormFields />
            <CheckboxField
              errorMessage={validationErrors.acknowledgement as string}
              hasError={!!validationErrors.acknowledgement}
              name="acknowledgement"
              value="yes"
              checked={isChecked}
              onChange={handleCheckboxChange}
              label={
                <>
                  {t('auth.agreeTerms')} 
                  <a href="/agreement" target="_blank">
                    {t('auth.viewTerms')}
                  </a>
                </>
              }
            />
          </>
        );
      },
    },
  };

  const services = {
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
       phone_number: {
         order:2,
         dialCodeList: ['+86', '+852', '+1']
       },
       password: {
         order: 3
       },
       confirm_password: {
         order: 4
       }
     },
  };

  return (
    <Authenticator
      socialProviders={socialProviders}
      initialState="signIn"
      components={components}
      services={services}
      formFields={formFields} 
    >
      <>{cloneElement(children as ReactElement, { signOut })}</>
    </Authenticator>
  );
};

export default AuthAmplify;