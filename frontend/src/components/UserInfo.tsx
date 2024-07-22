import { Auth } from 'aws-amplify';
import { useState, useEffect } from 'react';

interface UserData {
  email: string;
  emailVerified: boolean;
  userId: string;
  [key: string]: any; // 为其他可能的属性留空间
}

// 自定义 hook 用于获取用户信息
export const useUserInfo = (): { user: UserData | null; loading: boolean; error: string | null } => {
  const [user, setUser] = useState<UserData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchUserInfo = async () => {
      try {
        const userData = await Auth.currentAuthenticatedUser();
        setUser({
          email: userData.attributes.email,
          emailVerified: userData.attributes.email_verified === 'true',
          userId: userData.attributes.sub,
          ...userData.attributes // 包含其他可能的属性
        });
      } catch (err) {
        setError('Failed to fetch user info');
        console.error('Error fetching user info:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchUserInfo();
  }, []);

  return { user, loading, error };
};

// 如果您想要导出一个默认值，可以直接导出 useUserInfo
export default useUserInfo;