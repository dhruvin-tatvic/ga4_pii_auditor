'use client';

import React, { useState, useEffect } from 'react';
import { Input } from '../ui/Input';
import { Button } from '../ui/Button';
import { Card, CardHeader, CardBody } from '../ui/Card';
import { SearchableSelect } from '../ui/SearchableSelect';
import { AuditPayload } from '../../types/audit';
import { triggerSingleAudit, fetchClientList } from '../../services/api';

interface Property {
  id: string;
  name: string;
  account_name: string;
}

interface ClientListItem {
  client_name: string;
  property_id: string;
  property_access: string;
  send_to: string;
  send_to_cc?: string;
}

const getLast7Days = () => {
  const end = new Date();
  const start = new Date();
  start.setDate(end.getDate() - 6);

  const formatDate = (date: Date) => date.toISOString().split('T')[0];

  return {
    start_date: formatDate(start),
    end_date: formatDate(end),
  };
};

export function AuditForm() {
  const [isLoading, setIsLoading] = useState(false);
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  const [clientList, setClientList] = useState<ClientListItem[]>([]);
  const [isLoadingClients, setIsLoadingClients] = useState(false);

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
    const loadClientList = async () => {
      setIsLoadingClients(true);
      try {
        const clients = await fetchClientList();
        setClientList(clients);
      } catch {
        setClientList([]);
      } finally {
        setIsLoadingClients(false);
      }
    };

    loadClientList();
  }, []);

  useEffect(() => {
    let active = true;
    if (formData.property_access) {
      const fetchProps = async () => {
        setIsLoadingProps(true);
        try {
          const res = await fetch(`/api/properties?access_email=${encodeURIComponent(formData.property_access)}`);
          const data = await res.json();
          if (active) {
            if (data.status === 'success') {
              setProperties(data.properties);
            } else {
              setProperties([]);
            }
          }
        } catch {
          if (active) setProperties([]);
        } finally {
          if (active) setIsLoadingProps(false);
        }
      };
      fetchProps();
    } else {
      setTimeout(() => {
        if (active) setProperties([]);
      }, 0);
    }
    return () => { active = false; };
  }, [formData.property_access]);

  const handlePropertyChange = (propertyId: string) => {
    const matched = properties.find(p => p.id === propertyId);
    if (matched) {
      setFormData(prev => ({
        ...prev,
        property_id: matched.id,
        client_name: matched.account_name
      }));
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  const runAuditFromPayload = async (payload: AuditPayload) => {
    setIsLoading(true);
    setFeedback(null);

    const response = await triggerSingleAudit(payload);

    setIsLoading(false);
    if (response.status === 'success') {
      setFeedback({ type: 'success', message: 'Audit triggered successfully! Check your email.' });
    } else {
      setFeedback({ type: 'error', message: response.message });
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await runAuditFromPayload(formData);
  };

  const handleQuickAudit = async (client: ClientListItem) => {
    const { start_date, end_date } = getLast7Days();

    await runAuditFromPayload({
      client_name: client.client_name,
      property_id: client.property_id,
      property_access: client.property_access,
      start_date,
      end_date,
      send_to: client.send_to,
      send_to_cc: client.send_to_cc || '',
      custom_dimensions: [],
    });
  };

  const propertyOptions = properties.map(p => ({
    value: p.id,
    label: `${p.name} (${p.id})`
  }));

  return (
    <Card className="w-full max-w-6xl mx-auto">
      <CardHeader
        title="Trigger GA4 PII Audit"
        description="Use the form for custom runs or click a client button for a quick last-7-days audit."
      />
      <CardBody>
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
          <form onSubmit={handleSubmit} className="space-y-8">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="md:col-span-2 flex flex-col space-y-1.5">
                <label className="text-sm font-medium text-gray-700">Account Type</label>
                <select
                  name="property_access"
                  value={formData.property_access}
                  onChange={handleChange}
                  className="flex h-10 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select an account...</option>
                  <option value="data.analytics@tatvic.com">Data Analytics (data.analytics@tatvic.com)</option>
                  <option value="premium@tatvic.com">Premium (premium@tatvic.com)</option>
                  <option value="enterprise@tatvic.com">Enterprise (enterprise@tatvic.com)</option>
                  <option value="tvsm@tatvic.com">TVS (tvsm@tatvic.com)</option>
                  <option value="dhruvin@tatvic.com">Dhruvin (dhruvin@tatvic.com)</option>
                </select>
              </div>

              {formData.property_access && (
                <div className="md:col-span-2">
                  <SearchableSelect
                    label="GA4 Property"
                    options={propertyOptions}
                    value={formData.property_id}
                    onChange={handlePropertyChange}
                    isLoading={isLoadingProps}
                    placeholder="Select property..."
                  />
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

          <div className="border border-gray-200 rounded-xl bg-white p-4 h-full">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Client List</h2>
              <span className="text-xs text-gray-500">Last 7 days default</span>
            </div>

            {isLoadingClients ? (
              <div className="text-sm text-gray-500">Loading clients...</div>
            ) : clientList.length === 0 ? (
              <div className="text-sm text-gray-500">No clients found in the sheet.</div>
            ) : (
              <div className="space-y-3 max-h-[620px] overflow-y-auto pr-1">
                {clientList.map((client) => (
                  <button
                    key={`${client.client_name}-${client.property_id}`}
                    type="button"
                    onClick={() => handleQuickAudit(client)}
                    disabled={isLoading}
                    className="w-full text-left rounded-lg border border-gray-200 bg-gray-50 p-3 hover:bg-blue-50 hover:border-blue-200 transition disabled:opacity-60 disabled:cursor-not-allowed"
                  >
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <div className="font-medium text-gray-900">{client.client_name}</div>
                        <div className="text-xs text-gray-500">Property ID: {client.property_id}</div>
                      </div>
                      <span className="rounded bg-blue-100 px-2 py-1 text-xs font-medium text-blue-700">Run</span>
                    </div>
                    <div className="mt-2 text-xs text-gray-500">
                      {client.property_access ? `Access: ${client.property_access}` : 'Default access'}
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </CardBody>
    </Card>
  );
}
