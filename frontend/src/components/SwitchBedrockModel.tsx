import React, { useState, useMemo, useEffect, useRef } from 'react';
import { twMerge } from 'tailwind-merge';
import { BaseProps } from '../@types/common';
import useModel from '../hooks/useModel';
import Button from './Button';

type Props = BaseProps;

const SwitchBedrockModel: React.FC<Props> = (props) => {
  const { availableModels, modelId, setModelId } = useModel();
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const defaultPreferredModel = "Claude 3.5";
  const preferredModel = useMemo(() => {
    return availableModels.find(model => 
      model.label.toLowerCase().includes(defaultPreferredModel.toLowerCase())
    ) || availableModels[0];
  }, [availableModels, defaultPreferredModel]);

  const otherModels = useMemo(() => 
    availableModels.filter(model => model.modelId !== preferredModel.modelId),
    [availableModels, preferredModel]
  );

  const selectedOtherModel = otherModels.find(model => model.modelId === modelId);

  useEffect(() => {
    if (!modelId) {
      setModelId(preferredModel.modelId);
    }
  }, [modelId, preferredModel, setModelId]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  return (
    <div
      className={twMerge(
        props.className,
        'flex justify-center gap-2 rounded-lg border border-light-gray bg-light-gray p-1 text-sm'
      )}>
      <Button
        className={twMerge(
          'flex w-40 flex-1 items-center justify-center rounded-lg p-2',
          modelId === preferredModel.modelId
            ? 'bg-aws-sea-blue text-aws-font-color-white'
            : 'bg-white text-dark-gray border border-aws-squid-ink/50'
        )}
        onClick={() => setModelId(preferredModel.modelId)}
      >
        <span>{preferredModel.label}</span>
      </Button>
      
      <div className="relative inline-block w-40" ref={dropdownRef}>
        <Button
          className={twMerge(
            'flex w-full items-center justify-between rounded-lg p-2',
            modelId !== preferredModel.modelId
              ? 'bg-aws-sea-blue text-aws-font-color-white'
              : 'bg-white text-dark-gray border border-aws-squid-ink/50'
          )}
          onClick={() => setIsDropdownOpen(!isDropdownOpen)}
        >
          <span>{selectedOtherModel ? selectedOtherModel.label : 'Other Models'}</span>
          <span>▼</span>
        </Button>
        
        {isDropdownOpen && (
          <div className="absolute right-0 mt-2 w-full rounded-md shadow-lg bg-white z-10">
            <div className="py-1">
              {otherModels.map((model) => (
                <button
                  key={model.modelId}
                  className="block w-full text-left px-4 py-2 text-sm hover:bg-gray-100"
                  onClick={() => {
                    setModelId(model.modelId);
                    setIsDropdownOpen(false);
                  }}
                >
                  {model.label}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SwitchBedrockModel;