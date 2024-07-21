import React, { useState, useCallback, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate, Link } from 'react-router-dom';
import Button from '../components/Button';
import { PiCheckCircle, PiArrowLeft } from 'react-icons/pi';
import ChatMessageMarkdown from '../components/ChatMessageMarkdown';

const UsrAgreement: React.FC = () => {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const [agreed, setAgreed] = useState(false);
  const [content, setContent] = useState('');

  useEffect(() => {
    const fetchContent = async () => {
      try {
        const response = await fetch(`/content/user-agreement-${i18n.language}.md`);
        const text = await response.text();
        setContent(text);
      } catch (error) {
        console.error('Failed to fetch agreement content:', error);
      }
    };

    fetchContent();
  }, [i18n.language]);

  const handleAgree = useCallback(() => {
    setAgreed(true);
    // 这里可以添加逻辑来记录用户已同意协议
    // 例如，可以设置一个本地存储标志或发送到服务器
    setTimeout(() => navigate('/'), 1500);
  }, [navigate]);

  return (
    <div className="container mx-auto px-4 py-8">
      <Link to="/" className="flex items-center text-aws-sea-blue hover:underline mb-4">
        <PiArrowLeft className="mr-2" />
        {t('common.backToHome')}
      </Link>
      <h1 className="text-3xl font-bold mb-6 text-aws-font-color">{t('usrAgreement.pageTitle')}</h1>
      <ChatMessageMarkdown className="markdown-content" messageId="user-agreement">
        {content}
      </ChatMessageMarkdown>
      <div className="mt-8 flex flex-col items-center">
        {!agreed ? (
          <Button
            onClick={handleAgree}
            icon={<PiCheckCircle />}
            className="bg-aws-sea-blue text-white"
          >
            {t('usrAgreement.agreeButton')}
          </Button>
        ) : (
          <div className="flex items-center text-green-600">
            <PiCheckCircle className="mr-2" />
            <span>{t('usrAgreement.agreedMessage')}</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default UsrAgreement;