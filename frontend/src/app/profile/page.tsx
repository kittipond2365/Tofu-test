'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  User,
  Mail,
  Phone,
  Trophy,
  Save,
  AlertCircle,
  Check,
  Settings,
  Camera,
  TrendingUp,
  Calendar,
  Activity,
  Edit2,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { apiClient } from '@/lib/api';
import { ProtectedLayout } from '@/components/layout/protected-layout';
import { Navbar } from '@/components/layout/navbar';
import { PageHeader, StatsCard } from '@/components/shared';
import { WinRateChart, RatingTrendChart, MatchesPerMonthChart } from '@/components/charts';
import { useAuthStore } from '@/stores/authStore';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { EmptyState } from '@/components/shared';
import { useToast } from '@/components/ui/Toast';

interface ProfileUpdateData {
  display_name?: string;
  full_name?: string;
  email?: string;
  phone?: string;
}

export default function ProfilePage() {
  const user = useAuthStore((s) => s.user);
  const setUser = useAuthStore((s) => s.setUser);
  const queryClient = useQueryClient();
  const { success, error: showError } = useToast();
  const [isEditing, setIsEditing] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'settings'>('overview');

  const [formData, setFormData] = useState<ProfileUpdateData>({
    display_name: user?.display_name || '',
    full_name: user?.full_name || '',
    email: user?.email || '',
    phone: user?.phone || '',
  });

  // Get user stats
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['profileStats', user?.id],
    queryFn: () => apiClient.getUserStats(user?.id || ''),
    enabled: !!user?.id,
  });

  // Update profile mutation
  const updateMutation = useMutation({
    mutationFn: (data: ProfileUpdateData) => apiClient.updateProfile(data),
    onSuccess: (updatedUser) => {
      setUser(updatedUser);
      queryClient.invalidateQueries({ queryKey: ['profileStats'] });
      setIsEditing(false);
      success('บันทึกข้อมูลสำเร็จ', 'ข้อมูลโปรไฟล์ของคุณถูกอัปเดตแล้ว');
    },
    onError: () => {
      showError('เกิดข้อผิดพลาด', 'ไม่สามารถบันทึกข้อมูลได้ กรุณาลองใหม่อีกครั้ง');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateMutation.mutate(formData);
  };

  const totalMatches = stats?.total_matches ?? user?.total_matches ?? 0;
  const wins = stats?.wins ?? user?.wins ?? 0;
  const losses = stats?.losses ?? user?.losses ?? 0;
  const rating = stats?.rating ?? user?.rating ?? 1000;

  // Mock data for charts
  const ratingHistory = [
    { date: 'ม.ค.', rating: 1000, matches: 5 },
    { date: 'ก.พ.', rating: 1025, matches: 8 },
    { date: 'มี.ค.', rating: 1010, matches: 6 },
    { date: 'เม.ย.', rating: 1045, matches: 10 },
    { date: 'พ.ค.', rating: 1030, matches: 7 },
    { date: 'มิ.ย.', rating: rating, matches: stats?.matches_this_month || 0 },
  ];

  const matchesPerMonth = [
    { month: 'ม.ค.', matches: 8 },
    { month: 'ก.พ.', matches: 12 },
    { month: 'มี.ค.', matches: 10 },
    { month: 'เม.ย.', matches: 15 },
    { month: 'พ.ค.', matches: 11 },
    { month: 'มิ.ย.', matches: stats?.matches_this_month || 0 },
  ];

  return (
    <ProtectedLayout>
      <Navbar />

      <main className="page-container">
        {/* Header */}
        <PageHeader
          title="โปรไฟล์ของฉัน"
          subtitle="จัดการข้อมูลส่วนตัวและดูสถิติ"
          breadcrumbs={[{ label: 'โปรไฟล์' }]}
        />

        <div className="grid gap-6 lg:grid-cols-3">
          {/* Left Column - Profile */}
          <div className="lg:col-span-1 space-y-6">
            {/* Profile Card */}
            <div className="glass-card overflow-hidden">
              {/* Cover Image */}
              <div className="h-32 bg-gradient-to-r from-emerald-500 via-teal-500 to-cyan-500 relative">
                <button className="absolute bottom-3 right-3 p-2 bg-white/20 hover:bg-white/30 rounded-lg text-white transition-colors">
                  <Camera className="w-4 h-4" />
                </button>
              </div>

              {/* Avatar & Info */}
              <div className="px-6 pb-6">
                <div className="relative -mt-12 mb-4">
                  <div className="w-24 h-24 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center text-white text-3xl font-bold border-4 border-white shadow-xl">
                    {user?.avatar_url ? (
                      <img
                        src={user.avatar_url}
                        alt={user.display_name}
                        className="w-full h-full rounded-xl object-cover"
                      />
                    ) : (
                      user?.display_name?.[0] || 'U'
                    )}
                  </div>
                  <button className="absolute bottom-0 right-0 p-1.5 bg-white rounded-lg shadow-md text-neutral-600 hover:text-neutral-900 border border-neutral-100">
                    <Camera className="w-4 h-4" />
                  </button>
                </div>

                <h2 className="text-xl font-bold text-neutral-900">{user?.display_name}</h2>
                <p className="text-neutral-500">{user?.full_name}</p>

                <div className="mt-4 pt-4 border-t border-neutral-100 space-y-2">
                  {user?.email && (
                    <div className="flex items-center gap-2 text-sm text-neutral-600">
                      <Mail className="w-4 h-4 text-neutral-400" />
                      {user.email}
                    </div>
                  )}
                  {user?.phone && (
                    <div className="flex items-center gap-2 text-sm text-neutral-600">
                      <Phone className="w-4 h-4 text-neutral-400" />
                      {user.phone}
                    </div>
                  )}
                </div>

                {!user?.email && (
                  <div className="mt-4 p-3 bg-amber-50 border border-amber-100 rounded-xl">
                    <p className="text-sm text-amber-700">
                      เพิ่มอีเมลเพื่อรับการแจ้งเตือนกิจกรรม
                    </p>
                  </div>
                )}

                <Button
                  variant="secondary"
                  className="w-full mt-4"
                  onClick={() => {
                    setActiveTab('settings');
                    setIsEditing(true);
                  }}
                >
                  <Edit2 className="w-4 h-4" />
                  แก้ไขโปรไฟล์
                </Button>
              </div>
            </div>

            {/* Quick Stats */}
            <div className="glass-card p-6">
              <h3 className="font-bold text-neutral-900 mb-4">สถิติรวม</h3>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-neutral-500 text-sm">Rating</span>
                  <span className="font-bold text-emerald-600 text-lg">{rating}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-neutral-500 text-sm">แมทช์ทั้งหมด</span>
                  <span className="font-bold text-neutral-900">{totalMatches}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-neutral-500 text-sm">ชนะ</span>
                  <span className="font-bold text-emerald-600">{wins}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-neutral-500 text-sm">แพ้</span>
                  <span className="font-bold text-rose-600">{losses}</span>
                </div>
                <div className="pt-3 border-t border-neutral-100">
                  <div className="flex justify-between items-center">
                    <span className="text-neutral-500 text-sm">อัตราชนะ</span>
                    <span className="font-bold text-violet-600">
                      {totalMatches > 0 ? ((wins / totalMatches) * 100).toFixed(1) : 0}%
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column - Stats & Charts */}
          <div className="lg:col-span-2 space-y-6">
            {/* Tabs */}
            <div className="flex gap-1 bg-neutral-100/80 p-1 rounded-xl w-fit">
              <button
                onClick={() => setActiveTab('overview')}
                className={cn(
                  'px-4 py-2 rounded-lg text-sm font-medium transition-all',
                  activeTab === 'overview'
                    ? 'bg-white text-neutral-900 shadow-sm'
                    : 'text-neutral-600 hover:text-neutral-900'
                )}
              >
                ภาพรวม
              </button>
              <button
                onClick={() => setActiveTab('settings')}
                className={cn(
                  'px-4 py-2 rounded-lg text-sm font-medium transition-all',
                  activeTab === 'settings'
                    ? 'bg-white text-neutral-900 shadow-sm'
                    : 'text-neutral-600 hover:text-neutral-900'
                )}
              >
                ตั้งค่า
              </button>
            </div>

            {activeTab === 'overview' && (
              <>
                {/* Stats Cards */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <StatsCard title="Rating" value={rating} icon={Trophy} color="amber" />
                  <StatsCard title="แมทช์รวม" value={totalMatches} icon={Activity} color="blue" />
                  <StatsCard
                    title="แมทช์เดือนนี้"
                    value={stats?.matches_this_month || 0}
                    icon={Calendar}
                    color="emerald"
                  />
                  <StatsCard
                    title="อัตราชนะ"
                    value={`${totalMatches > 0 ? ((wins / totalMatches) * 100).toFixed(0) : 0}%`}
                    icon={TrendingUp}
                    color="purple"
                  />
                </div>

                {/* Charts Row */}
                <div className="grid md:grid-cols-2 gap-6">
                  {/* Win Rate Chart */}
                  <div className="glass-card p-6">
                    <h3 className="text-lg font-bold text-neutral-900 mb-4">สถิติ ชนะ/แพ้</h3>
                    <div className="flex justify-center">
                      <WinRateChart wins={wins} losses={losses} size={200} />
                    </div>
                  </div>

                  {/* Rating Trend */}
                  <div className="glass-card p-6">
                    <h3 className="text-lg font-bold text-neutral-900 mb-4">แนวโน้ม Rating</h3>
                    <RatingTrendChart data={ratingHistory} height={200} />
                  </div>
                </div>

                {/* Matches Per Month */}
                <div className="glass-card p-6">
                  <h3 className="text-lg font-bold text-neutral-900 mb-4">จำนวนแมทช์ต่อเดือน</h3>
                  <MatchesPerMonthChart data={matchesPerMonth} height={250} />
                </div>
              </>
            )}

            {activeTab === 'settings' && (
              <div className="glass-card p-6">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-lg font-bold text-neutral-900">ข้อมูลส่วนตัว</h2>
                </div>

                {isEditing ? (
                  <form onSubmit={handleSubmit} className="space-y-5">
                    <Input
                      label="ชื่อที่แสดง"
                      value={formData.display_name}
                      onChange={(e) =>
                        setFormData({ ...formData, display_name: e.target.value })
                      }
                      placeholder="ชื่อที่แสดงในระบบ"
                      leftIcon={<User className="w-5 h-5" />}
                    />

                    <Input
                      label="ชื่อ-นามสกุล"
                      value={formData.full_name}
                      onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                      placeholder="ชื่อ-นามสกุลจริง"
                      leftIcon={<User className="w-5 h-5" />}
                    />

                    <Input
                      label="อีเมล"
                      type="email"
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      placeholder="your@email.com"
                      leftIcon={<Mail className="w-5 h-5" />}
                      helpText="ใช้สำหรับรับการแจ้งเตือน"
                    />

                    <Input
                      label="เบอร์โทรศัพท์"
                      type="tel"
                      value={formData.phone}
                      onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                      placeholder="081-234-5678"
                      leftIcon={<Phone className="w-5 h-5" />}
                    />

                    {/* Buttons */}
                    <div className="flex gap-3 pt-2">
                      <Button
                        type="submit"
                        isLoading={updateMutation.isPending}
                        loadingText="กำลังบันทึก..."
                      >
                        <Save className="w-4 h-4" />
                        บันทึก
                      </Button>
                      <Button
                        type="button"
                        variant="secondary"
                        onClick={() => {
                          setIsEditing(false);
                          setFormData({
                            display_name: user?.display_name || '',
                            full_name: user?.full_name || '',
                            email: user?.email || '',
                            phone: user?.phone || '',
                          });
                        }}
                      >
                        ยกเลิก
                      </Button>
                    </div>
                  </form>
                ) : (
                  <div className="space-y-4">
                    <div className="flex items-center gap-4 p-4 bg-neutral-50 rounded-xl">
                      <div className="w-10 h-10 rounded-xl bg-emerald-100 flex items-center justify-center">
                        <User className="w-5 h-5 text-emerald-600" />
                      </div>
                      <div className="flex-1">
                        <p className="text-sm text-neutral-500">ชื่อที่แสดง</p>
                        <p className="font-semibold text-neutral-900">{user?.display_name || '-'}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4 p-4 bg-neutral-50 rounded-xl">
                      <div className="w-10 h-10 rounded-xl bg-purple-100 flex items-center justify-center">
                        <User className="w-5 h-5 text-purple-600" />
                      </div>
                      <div className="flex-1">
                        <p className="text-sm text-neutral-500">ชื่อ-นามสกุล</p>
                        <p className="font-semibold text-neutral-900">{user?.full_name || '-'}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4 p-4 bg-neutral-50 rounded-xl">
                      <div className="w-10 h-10 rounded-xl bg-blue-100 flex items-center justify-center">
                        <Mail className="w-5 h-5 text-blue-600" />
                      </div>
                      <div className="flex-1">
                        <p className="text-sm text-neutral-500">อีเมล</p>
                        <p className="font-semibold text-neutral-900">{user?.email || 'ยังไม่ได้เพิ่ม'}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4 p-4 bg-neutral-50 rounded-xl">
                      <div className="w-10 h-10 rounded-xl bg-amber-100 flex items-center justify-center">
                        <Phone className="w-5 h-5 text-amber-600" />
                      </div>
                      <div className="flex-1">
                        <p className="text-sm text-neutral-500">เบอร์โทรศัพท์</p>
                        <p className="font-semibold text-neutral-900">{user?.phone || 'ยังไม่ได้เพิ่ม'}</p>
                      </div>
                    </div>

                    <Button className="w-full mt-4" onClick={() => setIsEditing(true)}>
                      <Edit2 className="w-4 h-4" />
                      แก้ไขข้อมูล
                    </Button>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </main>
    </ProtectedLayout>
  );
}