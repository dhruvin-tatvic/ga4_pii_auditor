import React, { useState, useRef, useEffect } from 'react';

export interface Option {
  value: string;
  label: string;
}

interface SearchableSelectProps {
  options: Option[];
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  label?: string;
  isLoading?: boolean;
}

export function SearchableSelect({ options, value, onChange, placeholder, label, isLoading }: SearchableSelectProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState('');
  const wrapperRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const filteredOptions = options.filter(option =>
    option.label.toLowerCase().includes(search.toLowerCase())
  );

  const selectedOption = options.find(o => o.value === value);

  return (
    <div className="flex flex-col space-y-1.5 w-full" ref={wrapperRef}>
      {label && (
        <label className="text-sm font-medium text-gray-700 flex items-center justify-between">
          <span>{label} {isLoading && <span className="text-xs animate-pulse text-blue-500 font-normal ml-2">(Loading...)</span>}</span>
        </label>
      )}
      <div className="relative w-full">
        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          className="flex h-10 w-full items-center justify-between rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-left focus:outline-none focus:ring-2 focus:ring-blue-500 shadow-sm"
        >
          <span className={`block truncate ${selectedOption ? 'text-gray-900' : 'text-gray-400'}`}>
            {selectedOption ? selectedOption.label : (placeholder || 'Select property...')}
          </span>
          <svg className="h-4 w-4 text-gray-400 shrink-0 ml-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={isOpen ? "M5 15l7-7 7 7" : "M19 9l-7 7-7-7"} />
          </svg>
        </button>

        {isOpen && (
          <div className="absolute z-10 mt-1 w-full rounded-md border border-gray-300 bg-white shadow-lg overflow-hidden">
            <div className="p-2 border-b border-gray-100 bg-gray-50">
              <input
                type="text"
                className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                placeholder="Search..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                onClick={(e) => e.stopPropagation()}
                autoFocus
              />
            </div>
            <ul className="max-h-60 overflow-auto py-1">
              {filteredOptions.length > 0 ? (
                filteredOptions.map((option) => (
                  <li
                    key={option.value}
                    className={`cursor-pointer px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 hover:text-gray-900 ${value === option.value ? 'bg-blue-50 text-blue-900 font-medium' : ''}`}
                    onClick={() => {
                      onChange(option.value);
                      setIsOpen(false);
                      setSearch('');
                    }}
                  >
                    {option.label}
                  </li>
                ))
              ) : (
                <li className="px-3 py-3 text-sm text-gray-500 text-center italic">No properties found.</li>
              )}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
