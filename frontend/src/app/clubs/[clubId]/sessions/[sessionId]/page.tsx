'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { 
  Calendar, MapPin, Clock, Users, ChevronLeft, Plus,
  CheckCircle, UserCheck, UserX, Trophy, Play, Check,
  AlertCircle
} from 'lucide-react';
import { apiClient } from '@/lib/api';
import { ProtectedLayout } from '@/components/layout/protected-layout';
import { Navbar } from '@/components/layout/navbar';
import { PageHeader, EmptyState, LoadingSkeleton } from '@/components/shared';
import { MatchCard } from '@/components/features/MatchCard';
import type { SessionStatus, RegistrationStatus } from '@/lib/types';

const statusConfig: Record<SessionStatus, { 
  label: string; 
  className: string;
  description: string;
}> = {
  draft: { 
    label: 'ร่าง', 
    className: 'bg-gray-100 text-gray-700',
    description: 'นัดตียังไม่เปิดให้สมัคร'
  },
  upcoming: { 
    label: 'เร็วๆ นี้', 
    className: 'bg-blue-100 text-blue-700',
    description: 'นัดตีจะเปิดให้สมัครเร็วๆ นี้'
  },
  open: { 
    label: 'เปิดรับสมัคร', 
    className: 'bg-green-100 text-green-700',
    description: 'สามารถสมัครเข้าร่วมได้'
  },
  full: { 
    label: 'เต็ม', 
    className: 'bg-amber-100 text-amber-700',
    description: 'ผู้เข้าร่วมเต็มแล้ว สามารถเข้าคิวรอได้'
  },
  active: { 
    label: 'กำลังดำเนินการ', 
    className: 'bg-purple-100 text-purple-700',
    description: 'นัดตีกำลังดำเนินการอยู่'
  },
  ongoing: { 
    label: 'กำลังแข่ง', 
    className: 'bg-blue-100 text-blue-700',
    description: 'นัดตีกำลังดำเนินอยู่'
  },
  completed: { 
    label: 'เสร็จสิ้น', 
    className: 'bg-gray-100 text-gray-700',
    description: 'นัดตีสิ้นสุดแล้ว'
  },
  cancelled: { 
    label: 'ยกเลิก', 
    className: 'bg-red-100 text-red-700',
    description: 'นัดตีถูกยกเลิก'
  },
};

const registrationStatusConfig: Record<RegistrationStatus, { 
  label: string; 
  className: string;
}> = {
  confirmed: { label: 'ยืนยัน', className: 'bg-green-100 text-green-700' },
  waitlisted: { label: 'รอคิว', className: 'bg-amber-100 text-amber-700' },
  cancelled: { label: 'ยกเลิก', className: 'bg-red-100 text-red-700' },
  attended: { label: 'เข้าร่วม', className: 'bg-blue-100 text-blue-700' },
  no_show: { label: 'ไม่มา', className: 'bg-gray-100 text-gray-700' },
};

export default function SessionDetailPage({ params }: { params: { clubId: string; sessionId: string } }) {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<'info' | 'participants' | 'matches'>('info');

  const { data: session, isLoading } = useQuery({
    queryKey: ['session', params.sessionId],
    queryFn: () => apiClient.getSession(params.sessionId)
  });

  const { data: matches, isLoading: matchesLoading } = useQuery({
    queryKey: ['matches', params.sessionId],
    queryFn: () => apiClient.getMatches(params.sessionId)
  });

  const { data: club } = useQuery({
    queryKey: ['club', params.clubId],
    queryFn: () => apiClient.getClub(params.clubId)
  });

  // Mutations
  const registerMutation = useMutation({
    mutationFn: () => apiClient.registerForSession(params.sessionId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['session', params.sessionId] })
  });

  const cancelMutation = useMutation({
    mutationFn: () => apiClient.cancelRegistration(params.sessionId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['session', params.sessionId] })
  });

  const checkInMutation = useMutation({
    mutationFn: () => apiClient.checkIn(params.sessionId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['session', params.sessionId] })
  });

  const checkOutMutation = useMutation({
    mutationFn: () => apiClient.checkOut(params.sessionId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['session', params.sessionId] })
  });

  const createMatchMutation = useMutation({
    mutationFn: () => apiClient.createMatch(params.sessionId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['matches', params.sessionId] })
  });

  const myRegistration = session?.registrations?.find(r => 
    ['confirmed', 'waitlisted', 'attended'].includes(r.status)
  );

  const isRegistered = !!myRegistration;
  const status = session ? statusConfig[session.status] : null;

  if (isLoading) {
    return (
      <ProtectedLayout>
        <Navbar />
        <main className="page-container">
          <LoadingSkeleton type="page" />
        </main>
      </ProtectedLayout>
    );
  }

  if (!session) {
    return (
      <ProtectedLayout>
        <Navbar />
        <main className="page-container">
          <EmptyState
            icon={AlertCircle}
            title="ไม่พบนัดตี"
            description="นัดตีนี้อาจถูกลบหรือคุณไม่มีสิทธิ์เข้าถึง"
            action={{ label: 'กลับไปหน้านัดตี', href: `/clubs/${params.clubId}/sessions` }}
          />
        </main>
      </ProtectedLayout>
    );
  }

  const startDate = new Date(session.start_time);
  const endDate = new Date(session.end_time);
  const fillPercentage = Math.min(100, Math.round((session.confirmed_count / session.max_participants) * 100));

  return (
    <ProtectedLayout>
      <Navbar />
      
      <main className="page-container">
        {/* Header */}
        <PageHeader
          title={session.title}
          subtitle={club?.name}
          breadcrumbs={[
            { label: 'ก๊วน', href: '/clubs' },
            { label: club?.name || '', href: `/clubs/${params.clubId}` },
            { label: 'นัดตี', href: `/clubs/${params.clubId}/sessions` },
            { label: session.title }
          ]}
          action={
            <Link 
              href={`/clubs/${params.clubId}/sessions`}
              className="btn-secondary flex items-center gap-2"
            >
              <ChevronLeft className="w-4 h-4" />
              กลับ
            </Link>
          }
        />

        {/* Status Banner */}
        <div className={`mb-6 p-4 rounded-xl ${status?.className} bg-opacity-50 border`}>
          <div className="flex items-center gap-3">
            <div className={`px-3 py-1 rounded-full text-sm font-medium ${status?.className}`}>
              {status?.label}
            </div>
            <p className="text-sm">{status?.description}</p>
          </div>
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Session Info Card */}
            <div className="card-modern p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                รายละเอียดนัดตี
              </h2>
              
              <div className="grid gap-4">
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center flex-shrink-0">
                    <Calendar className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">วันที่</p>
                    <p className="font-medium text-gray-900">
                      {startDate.toLocaleDateString('th-TH', {
                        weekday: 'long',
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric',
                      })}
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 rounded-lg bg-green-100 flex items-center justify-center flex-shrink-0">
                    <Clock className="w-5 h-5 text-green-600" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">เวลา</p>
                    <p className="font-medium text-gray-900">
                      {startDate.toLocaleTimeString('th-TH', { hour: '2-digit', minute: '2-digit' })} - 
                      {endDate.toLocaleTimeString('th-TH', { hour: '2-digit', minute: '2-digit' })}
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 rounded-lg bg-amber-100 flex items-center justify-center flex-shrink-0">
                    <MapPin className="w-5 h-5 text-amber-600" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">สถานที่</p>
                    <p className="font-medium text-gray-900">{session.location}</p>
                  </div>
                </div>

                {session.description && (
                  <div className="mt-4 pt-4 border-t border-gray-100">
                    <p className="text-sm text-gray-500 mb-2">คำอธิบาย</p>
                    <p className="text-gray-700">{session.description}</p>
                  </div>
                )}
              </div>
            </div>

            {/* Matches Section */}
            <div className="card-modern p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                  <Trophy className="w-5 h-5 text-amber-500" />
                  แมทช์
                </h2>
                <button
                  onClick={() => createMatchMutation.mutate()}
                  disabled={createMatchMutation.isPending}
                  className="btn-primary text-sm flex items-center gap-2 disabled:opacity-50"
                >
                  <Plus className="w-4 h-4" />
                  สร้างแมทช์
                </button>
              </div>

              {matchesLoading ? (
                <div className="space-y-3">
                  <div className="h-20 bg-gray-100 rounded-lg animate-pulse" />
                  <div className="h-20 bg-gray-100 rounded-lg animate-pulse" />
                </div>
              ) : matches && matches.length > 0 ? (
                <div className="space-y-3">
                  {matches.map((match) => (
                    <MatchCard key={match.id} match={match} />
                  ))}
                </div>
              ) : (
                <EmptyState
                  icon={Trophy}
                  title="ยังไม่มีแมทช์"
                  description="สร้างแมทช์แรกสำหรับนัดตีนี้"
                />
              )}
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Registration Card */}
            <div className="card-modern p-6">
              <h3 className="font-semibold text-gray-900 mb-4">การลงทะเบียน</h3>
              
              {/* Progress */}
              <div className="mb-4">
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-gray-600">จำนวนผู้เข้าร่วม</span>
                  <span className="font-medium">
                    {session.confirmed_count} / {session.max_participants}
                  </span>
                </div>
                <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-blue-500 rounded-full transition-all"
                    style={{ width: `${fillPercentage}%` }}
                  />
                </div>
                {session.waitlist_count > 0 && (
                  <p className="text-xs text-amber-600 mt-2">
                    มี {session.waitlist_count} คนอยู่ในรายการรอ
                  </p>
                )}
              </div>

              {/* Actions */}
              <div className="space-y-2">
                {!isRegistered ? (
                  <button
                    onClick={() => registerMutation.mutate()}
                    disabled={registerMutation.isPending || session.status !== 'open'}
                    className="w-full btn-primary disabled:opacity-50"
                  >
                    {registerMutation.isPending ? 'กำลังสมัคร...' : 'สมัครเข้าร่วม'}
                  </button>
                ) : (
                  <>
                    <div className="p-3 bg-green-50 rounded-lg mb-2">
                      <p className="text-sm text-green-700 flex items-center gap-2">
                        <CheckCircle className="w-4 h-4" />
                        คุณได้ลงทะเบียนแล้ว
                        {myRegistration?.status === 'waitlisted' && ' (รอคิว)'}
                      </p>
                    </div>
                    <button
                      onClick={() => cancelMutation.mutate()}
                      disabled={cancelMutation.isPending}
                      className="w-full btn-secondary text-red-600 border-red-200 hover:bg-red-50 disabled:opacity-50"
                    >
                      {cancelMutation.isPending ? 'กำลังยกเลิก...' : 'ยกเลิกการลงทะเบียน'}
                    </button>
                  </>
                )}

                {isRegistered && (
                  <div className="flex gap-2 pt-2">
                    <button
                      onClick={() => checkInMutation.mutate()}
                      disabled={checkInMutation.isPending}
                      className="flex-1 py-2 px-3 bg-green-100 text-green-700 rounded-lg text-sm font-medium hover:bg-green-200 transition-colors disabled:opacity-50"
                    >
                      <UserCheck className="w-4 h-4 mx-auto mb-1" />
                      เช็คอิน
                    </button>
                    <button
                      onClick={() => checkOutMutation.mutate()}
                      disabled={checkOutMutation.isPending}
                      className="flex-1 py-2 px-3 bg-gray-100 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-200 transition-colors disabled:opacity-50"
                    >
                      <UserX className="w-4 h-4 mx-auto mb-1" />
                      เช็คเอาท์
                    </button>
                  </div>
                )}
              </div>
            </div>

            {/* Participants List */}
            <div className="card-modern p-6">
              <h3 className="font-semibold text-gray-900 mb-4">
                ผู้เข้าร่วม ({session.registrations?.length || 0})
              </h3>
              
              {session.registrations && session.registrations.length > 0 ? (
                <div className="space-y-3 max-h-[400px] overflow-y-auto">
                  {session.registrations.map((reg) => {
                    const regStatus = registrationStatusConfig[reg.status];
                    return (
                      <div key={reg.id} className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-indigo-500 flex items-center justify-center text-white font-bold text-sm">
                          {(reg.display_name || reg.full_name).charAt(0)}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-gray-900 text-sm truncate">
                            {reg.display_name || reg.full_name}
                          </p>
                          <p className="text-xs text-gray-500">
                            {new Date(reg.registered_at).toLocaleDateString('th-TH')}
                          </p>
                        </div>
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${regStatus.className}`}>
                          {regStatus.label}
                          {reg.waitlist_position && ` #${reg.waitlist_position}`}
                        </span>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <p className="text-sm text-gray-500 text-center py-4">
                  ยังไม่มีผู้ลงทะเบียน
                </p>
              )}
            </div>
          </div>
        </div>
      </main>
    </ProtectedLayout>
  );
}
