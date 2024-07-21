import React, { useState, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate, Link } from 'react-router-dom';
import Button from '../components/Button';
import { PiCheckCircle, PiArrowLeft } from 'react-icons/pi';

const UsageRules: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [agreed, setAgreed] = useState(false);

  const handleAgree = useCallback(() => {
    setAgreed(true);
    // 这里可以添加逻辑来记录用户已同意规则
    // 例如，可以设置一个本地存储标志或发送到服务器
    setTimeout(() => navigate('/'), 1500);
  }, [navigate]);

  return (
    <div className="container mx-auto px-4 py-8">
      <Link to="/" className="flex items-center text-aws-sea-blue hover:underline mb-4">
        <PiArrowLeft className="mr-2" />
        {t('common.backToHome')}
      </Link>
      <h1 className="text-3xl font-bold mb-6 text-aws-font-color">{t('usageRules.pageTitle')}</h1>
      <div className="space-y-4">
        <section>
          <h2 className="text-xl font-semibold mb-2 text-aws-font-color">{t('usageRules.section1.title')}</h2>
          <p className="text-dark-gray">{t('usageRules.section1.content')}</p>
        </section>
        <section>
          <h2 className="text-xl font-semibold mb-2 text-aws-font-color">{t('usageRules.section2.title')}</h2>
          <p className="text-dark-gray">{t('usageRules.section2.content')}</p>
        </section>
        <section>
          <h2 className="text-xl font-semibold mb-2 text-aws-font-color">{t('usageRules.section3.title')}</h2>
          <ul className="list-disc pl-5 text-dark-gray">
            <li>{t('usageRules.section3.item1')}</li>
            <li>{t('usageRules.section3.item2')}</li>
            <li>{t('usageRules.section3.item3')}</li>
          </ul>
        </section>
      </div>
      <div className="mt-8 flex flex-col items-center">
        {!agreed ? (
          <Button
            onClick={handleAgree}
            icon={<PiCheckCircle />}
            className="bg-aws-sea-blue text-white"
          >
            {t('usageRules.agreeButton')}
          </Button>
        ) : (
          <div className="flex items-center text-green-600">
            <PiCheckCircle className="mr-2" />
            <span>{t('usageRules.agreedMessage')}</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default UsageRules;