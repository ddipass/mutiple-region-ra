import { twMerge } from 'tailwind-merge';
import { useTranslation } from 'react-i18next';
import { PiArrowDown } from 'react-icons/pi';
import { addDate, formatDate } from '../utils/DateUtils';
import React, { useMemo, useState } from 'react';
import Help from '../components/Help';
import Button from '../components/Button';
import InputText from '../components/InputText';
import Skeleton from '../components/Skeleton';
import ListItemUser from '../components/ListItemUser';
import useAdminUsers from '../hooks/useAdminUsers';


const DATA_FORMAT = 'YYYYMMDD';

const AdminUsersPage: React.FC = () => {
  const { t } = useTranslation();

  const [searchDateFrom, setSearchDateFrom] = useState<null | string>(
    formatDate(addDate(new Date(), -1, 'month'), DATA_FORMAT)
  );
  const [searchDateTo, setSearchDateTo] = useState<null | string>(
    formatDate(new Date(), DATA_FORMAT)
  );
  const [isDescCost, setIsDescCost] = useState(true);

  const { adminUsers, isLoading: isLoadingUsers } = useAdminUsers({
    start: searchDateFrom ? searchDateFrom + '00' : undefined,
    end: searchDateTo ? searchDateTo + '23' : undefined,
  });

  const sortedUsers = useMemo(() => {
    const tmp = isDescCost ? -1 : 1;
    return adminUsers?.sort((a, b) =>
      a.totalPrice > b.totalPrice ? tmp : tmp * -1
    );
  }, [isDescCost, adminUsers]);

  const validationErrorMessage = useMemo(() => {
    return !!searchDateFrom === !!searchDateTo
      ? null
      : t('admin.validationError.period');
  }, [searchDateFrom, searchDateTo, t]);

  return (
    <>
      <div className="flex h-full justify-center">
        <div className="w-2/3">
          <div className="h-full w-full pt-8">
            <div className="flex items-end justify-between">
              <div className="flex items-center gap-2">
                <div className="text-xl font-bold">
                  {t('admin.usersManagement.label.pageTitle')}
                </div>
                <Help
                  direction="right"
                  message={t('admin.usersManagement.help.overview')}
                />
              </div>
            </div>

            <div className="my-2 rounded border p-2">
              <div className="flex items-center gap-1 text-sm font-bold">
                {t('admin.usersManagement.label.SearchCondition.title')}
                <Help
                  message={t('admin.usersManagement.help.calculationPeriod')}
                />
              </div>

              <div className="flex gap-2 sm:w-full md:w-3/4">
                <InputText
                  className="w-full"
                  type="date"
                  label={t(
                    'admin.usersManagement.label.SearchCondition.from'
                  )}
                  value={formatDate(searchDateFrom, 'YYYY-MM-DD')}
                  onChange={(val) => {
                    if (val === '') {
                      setSearchDateFrom(null);
                      return;
                    }
                    setSearchDateFrom(formatDate(val, DATA_FORMAT));
                  }}
                  errorMessage={
                    searchDateFrom
                      ? undefined
                      : validationErrorMessage ?? undefined
                  }
                />
                <InputText
                  className="w-full"
                  type="date"
                  label={t('admin.usersManagement.label.SearchCondition.to')}
                  value={formatDate(searchDateTo, 'YYYY-MM-DD')}
                  onChange={(val) => {
                    if (val === '') {
                      setSearchDateTo(null);
                      return;
                    }
                    setSearchDateTo(formatDate(val, DATA_FORMAT));
                  }}
                  errorMessage={
                    searchDateTo
                      ? undefined
                      : validationErrorMessage ?? undefined
                  }
                />
              </div>
            </div>

            <div className="my-2 flex justify-end">
              <Button
                outlined
                rightIcon={
                  <PiArrowDown
                    className={twMerge(
                      'transition',
                      isDescCost ? 'rotate-0' : 'rotate-180'
                    )}
                  />
                }
                onClick={() => {
                  setIsDescCost(!isDescCost);
                }}>
                {t('admin.sharedBotAnalytics.label.sortByCost')}
              </Button>
            </div>

            <div className="mt-2 border-b border-gray"></div>

            <div className="h-4/5 overflow-x-hidden overflow-y-scroll border-b border-gray pr-1 scrollbar-thin scrollbar-thumb-aws-font-color/20 ">
              {isLoadingUsers && (
                <div className="flex flex-col gap-2">
                  {new Array(15).fill('').map((_, idx) => {
                    return <Skeleton key={idx} className="h-12 w-full" />;
                  })}
                </div>
              )}

              {adminUsers?.length === 0 && (
                <div className="flex h-full w-full items-center justify-center italic text-dark-gray">
                  {t('admin.usersManagement.label.noUser')}
                </div>
              )}
              {sortedUsers?.map((user, idx) => (
                <ListItemUser
                  key={idx}
                  user={{
                    ...user,
                    available: true,
                    isAccurate: false,
                  }}>
                  <div className="relative flex h-full items-center">
                    <div className="text-lg font-bold">
                      {(Math.floor(user.totalPrice * 100) / 100).toFixed(2)} USD
                    </div>
                    <div className="absolute bottom-0 right-0 flex origin-bottom-right whitespace-nowrap text-xs font-light">
                      {user.isAccurate ? (
                        <>
                          {user.isAccurate
                            ? t('admin.usersManagement.help.calculationMemo')
                            : null}
                        </>
                      ) : (
                        <div></div>
                      )}
                    </div>
                  </div>
                </ListItemUser>
              ))}
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default AdminUsersPage;
