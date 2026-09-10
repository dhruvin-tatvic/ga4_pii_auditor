import os

content = """'use client';

import React, { useState, useEffect } from 'react';
import { Input } from '../ui/Input';
import { Button } from '../ui/Button';
import { Card, CardHeader, CardBody } from '../ui/Card';
import { AuditPayload } from '../../types/audit';
import { triggerSingleAudit } from '../../services/api';

interface Property {
  id: string;
  name: string;
  account_name: string;
}

export function AuditForm() {
  const [isLoading, setIsLoading] = useState(false);
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const [formData, setFormData] = useState<AuditPayload>({
    client_name: '',
    property_id: '',
    property_access: '',
    start_date: '',
    end_date: '',
    send_to: '',
    send_to_cc: '',
  });

  const [properties, setProperties] = useState<Property[]>([]);
  const [isLoadingProps, setIsLoadingProps] = useState(false);

  useEffect(() => {
    if (formData.property_access) {
      setIsLoadingProps(true);
      fetch(`/api/properties?access_email=${encodeURIComponent(formData.property_access)}`)
        .then(res => res.json())
        .then(data => {
          if (data.status === 'success') {
            setProperties(data.properties);
          } else {
            setProperties([]);
          }
        })
        .catch(() => setProperties([]))
        .finally(() => setIsLoadingProps(false));
    } else {
      setProperties([]);
    }
  }, [formData.property_access]);

  const handlePropertySelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    const matched = properties.find(p => `${p.name} (${p.id})` === val);
    if (matched) {
      setFormData(prev => ({
        ...prev,
        property_id: matched.id,
        client_name: prev.client_name || matched.account_name
      }));
      // Optional: clear the input after selection, but let's leave it so user sees their selection
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setFeedback(null);

    const response = await triggerSingleAudit(formData);

    setIsLoading(false);
    if (response.status === 'success') {
      setFeedback({ type: 'success', message: 'Audit triggered successfully! Check your email.' });
    } else {
      setFeedback({ type: 'error', message: response.message });
    }
  };

  return (
    <Card className="w-full max-w-4xl mx-auto">
      <CardHeader 
        title="Trigger GA4 PII Audit" 
        description="Fill out the details below to trigger an audit for a specific property." 
      />
      <CardBody>
        <form onSubmit={handleSubmit} className="space-y-8">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            
            <div className="md:col-span-2 flex flex-col space-y-1.5">
              <label className="text-sm font-medium text-gray-700">
                GA4 Property Access Account
              </label>
              <select
                name="property_access"
                value={formData.property_access}
                onChange={handleChange}
                className="flex h-10 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Select an account to fetch properties...</option>
                <option value="dhruvin@tatvic.com">dhruvin (dhruvin@tatvic.com)</option>
                <option value="data.analytics@tatvic.com">data.analytics (data.analytics@tatvic.com)</option>
                <option value="premium@tatvic.com">premium (premium@tatvic.com)</option>
                <option value="enterprise@tatvic.com">enterprise (enterprise@tatvic.com)</option>
                <option value="tvsm@tatvic.com">tvs (tvsm@tatvic.com)</option>
              </select>
            </div>
            
            {formData.property_access && (
              <div className="md:col-span-2 flex flex-col space-y-1.5 p-4 bg-blue-50 border border-blue-100 rounded-lg">
                <label className="text-sm font-medium text-blue-800">
                  Search & Select Property {isLoadingProps && <span className="text-xs animate-pulse ml-2">(Fetching properties...)</span>}
                </label>
                <input
                  list="property-list"
                  onChange={handlePropertySelect}
                  placeholder="Type property name or ID to auto-fill below..."
                  className="flex h-10 w-full rounded-md border border-blue-200 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <datalist id="property-list">
                  {properties.map(p => (
                    <option key={p.id} value={`${p.name} (${p.id})`}>{p.account_name}</option>
                  ))}
                </datalist>
                <p className="text-xs text-blue-600 mt-1">Selecting a property will auto-fill the Client Name and Property ID below.</p>
              </div>
            )}

            <Input label="Client Name" name="client_name" value={formData.client_name} onChange={handleChange} required placeholder="e.g. Acme Corp" />
            <Input label="GA4 Property ID" name="property_id" value={formData.property_id} onChange={handleChange} required placeholder="e.g. 123456789" />
            
            <div className="grid grid-cols-2 gap-4 md:col-span-2">
              <Input label="Start Date" name="start_date" type="date" value={formData.start_date} onChange={handleChange} />
              <Input label="End Date" name="end_date" type="date" value={formData.end_date} onChange={handleChange} />
            </div>

            <Input label="Send To (Email)" name="send_to" type="email" value={formData.send_to} onChange={handleChange} required placeholder="alert@acme.com" />
            <Input label="Send To CC (Email)" name="send_to_cc" type="email" value={formData.send_to_cc} onChange={handleChange} placeholder="team@acme.com" />
          </div>

          {feedback && (
            <div className={`p-4 rounded-lg ${feedback.type === 'success' ? 'bg-green-50 text-green-800 border border-green-200' : 'bg-red-50 text-red-800 border border-red-200'}`}>
              {feedback.message}
            </div>
          )}

          <div className="flex justify-end pt-4 border-t border-gray-100">
            <Button type="submit" isLoading={isLoading} className="w-full md:w-auto">
              Run Audit
            </Button>
          </div>
        </form>
      </CardBody>
    </Card>
  );
}
"""

with open("frontend/src/components/forms/AuditForm.tsx", "w") as f:
    f.write(content)
