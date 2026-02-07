'use client';

import { useRouter } from 'next/navigation';
import ChefHatIcon from '@/components/icons/ChefHatIcon';

export default function KitchenPage() {
  const router = useRouter();

  return (
    <div className="flex h-dvh items-center justify-center p-8">
      <div className="max-w-2xl">
        <div className="flex items-start gap-6">
          <ChefHatIcon className="w-20 h-20 text-primary flex-shrink-0" />
          <div>
            <h1 className="text-4xl font-bold text-text mb-3">Kitchen</h1>
            <p className="text-lg text-text/70 mb-6">
              Get step-by-step guidance while you cook with real-time assistance
            </p>
            <button
              onClick={() => router.push('/kitchen/new')}
              className="px-8 py-3 rounded-lg font-medium transition-all text-lg bg-primary text-white hover:bg-primary/90"
            >
              Start Cooking
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
