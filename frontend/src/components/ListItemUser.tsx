import { ReactNode } from 'react';
import { BaseProps } from '../@types/common';

type Props = BaseProps & {
  user: {
    id: string;
    email: string;
    description: string;
    available: boolean;
    isAccurate: boolean;
  };
  children: ReactNode;
};

const ListItemUser: React.FC<Props> = (props) => {
  return (
    <div
      key={props.user.id}
      className={`${
        props.className ?? ''
      } relative flex w-full justify-between border-b border-light-gray`}>
      <div
        className={`h-full grow bg-aws-paper p-2 ${
          props.user.available
            ? 'cursor-pointer hover:brightness-90'
            : 'text-aws-font-color/30'
        }`}>
        <div className="w-full overflow-hidden text-ellipsis text-sm font-semibold">
          {props.user.email}
        </div>
        <div className="mt-1 overflow-hidden text-ellipsis text-xs">
          {props.user.description}
        </div>
      </div>
      <div className="absolute right-0 flex h-full justify-between ">
        <div className="w-10 bg-gradient-to-r from-transparent to-aws-paper"></div>
        <div className="flex items-center  gap-2 bg-aws-paper pl-2">
          {props.children}
        </div>
      </div>
    </div>
  );
};

export default ListItemUser;
