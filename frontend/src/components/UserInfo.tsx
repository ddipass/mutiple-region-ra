import React, { useEffect, useState } from 'react';
import { Auth } from 'aws-amplify';

interface UserData {
  username: string;
  email: string;
  userId: string;
  emailVerified: boolean;
  phoneNumber?: string;
  createdAt: Date;
  updatedAt: Date;
  [key: string]: any; // 为其他可能的属性留空间
}

// 自定义 hook 用于获取用户信息
export const useUserInfo = () => {
  const [user, setUser] = useState<UserData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchUserInfo = async () => {
      try {
        const userData = await Auth.currentAuthenticatedUser();
        setUser({
          username: userData.username,
          email: userData.attributes.email,
          userId: userData.attributes.sub,
          emailVerified: userData.attributes.email_verified,
          phoneNumber: userData.attributes.phone_number,
          createdAt: new Date(userData.attributes.created_at),
          updatedAt: new Date(userData.attributes.updated_at),
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

// 使用 useUserInfo hook 的示例组件
const UserInfo: React.FC = () => {
  const { user, loading, error } = useUserInfo();

  if (loading) return <div>Loading user information...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!user) return <div>No user logged in</div>;

  return (
    <div>
      <h2>User Information</h2>
      <p><strong>Username:</strong> {user.username}</p>
      <p><strong>Email:</strong> {user.email}</p>
      <p><strong>User ID:</strong> {user.userId}</p>
      <p><strong>Email Verified:</strong> {user.emailVerified ? 'Yes' : 'No'}</p>
      {user.phoneNumber && <p><strong>Phone Number:</strong> {user.phoneNumber}</p>}
      <p><strong>Account Created:</strong> {user.createdAt.toLocaleString()}</p>
      <p><strong>Last Updated:</strong> {user.updatedAt.toLocaleString()}</p>
    </div>
  );
};

export default UserInfo;