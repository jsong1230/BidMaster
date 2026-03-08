'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

interface NavItem {
  href: string;
  label: string;
  icon: React.ReactNode;
}

const navItems: NavItem[] = [
  {
    href: '/dashboard',
    label: '대시보드',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
      </svg>
    ),
  },
];

/** 공고 섹션 메뉴 항목 */
const bidItems: NavItem[] = [
  {
    href: '/bids',
    label: '공고 목록',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
      </svg>
    ),
  },
  {
    href: '/bids/matched',
    label: '매칭 공고',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
      </svg>
    ),
  },
];

const settingsItems: NavItem[] = [
  {
    href: '/settings/company',
    label: '회사 프로필',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
      </svg>
    ),
  },
];

function NavLink({ item }: { item: NavItem }) {
  const pathname = usePathname();
  const isActive = pathname === item.href || pathname.startsWith(item.href + '/');

  return (
    <Link
      href={item.href}
      className={`flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
        isActive
          ? 'bg-blue-50 text-blue-700'
          : 'text-neutral-600 hover:bg-neutral-100 hover:text-neutral-900'
      }`}
    >
      <span className={isActive ? 'text-blue-600' : 'text-neutral-400'}>{item.icon}</span>
      {item.label}
    </Link>
  );
}

export default function Sidebar() {
  return (
    <aside className="w-64 flex-shrink-0 h-full border-r border-neutral-200 bg-white flex flex-col">
      {/* 로고 */}
      <div className="h-16 flex items-center px-6 border-b border-neutral-200">
        <Link href="/dashboard" className="text-lg font-bold text-blue-600">
          BidMaster
        </Link>
      </div>

      {/* 네비게이션 */}
      <nav className="p-4 space-y-1 flex-1 overflow-y-auto">
        {navItems.map((item) => (
          <NavLink key={item.href} item={item} />
        ))}

        {/* 공고 섹션 */}
        <div className="pt-3">
          <p className="px-3 pb-1 text-xs font-semibold text-neutral-400 uppercase tracking-wider">
            공고
          </p>
          <div className="space-y-1">
            {bidItems.map((item) => (
              <NavLink key={item.href} item={item} />
            ))}
          </div>
        </div>
      </nav>

      <div className="px-4">
        <div className="border-t border-neutral-200 pt-4">
          <p className="px-3 pb-2 text-xs font-semibold text-neutral-400 uppercase tracking-wider">
            설정
          </p>
          <div className="space-y-1">
            {settingsItems.map((item) => (
              <NavLink key={item.href} item={item} />
            ))}
          </div>
        </div>
      </div>
    </aside>
  );
}
