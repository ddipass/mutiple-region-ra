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
        const response = await fetch(`/user-agreement.md`);
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
    <div className="relative flex h-full flex-1 flex-col">
      {/* 1. 顶部区域 */}
      <div className="sticky top-0 z-10 mb-1.5 flex h-14 w-full items-center justify-between border-b border-gray bg-aws-paper p-2">
        <Link to="/" className="flex items-center text-aws-sea-blue hover:underline">
          <PiArrowLeft className="mr-2" />
          {t('common.backToHome')}
        </Link>
        <h1 className="text-xl font-bold text-aws-font-color">{t('usrAgreement.pageTitle')}</h1>
      </div>

      {/* 2. 内容区域 */}
      <section className="relative h-full w-full flex-1 overflow-auto pb-9">
        <div className="h-full">
          <div className="flex h-full flex-col overflow-auto pb-16">
            <div className="grid grid-cols-12 gap-2 p-3">
              <div className="order-first col-span-12 flex lg:order-none lg:col-span-8 lg:col-start-3">
                <div className="ml-5 grow ">
                    <ChatMessageMarkdown className="markdown-content" messageId="user-agreement">
                      {content}
                    </ChatMessageMarkdown>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 3. 底部区域 */}
      <div className="bottom-0 z-0 flex w-full flex-col items-center justify-center p-4">
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