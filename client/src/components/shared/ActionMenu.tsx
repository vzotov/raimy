'use client';

import * as DropdownMenu from '@radix-ui/react-dropdown-menu';
import React from 'react';

export interface ActionMenuItem {
  label: string;
  icon?: React.ReactNode;
  onClick: () => void;
  disabled?: boolean;
  destructive?: boolean;
}

interface ActionMenuProps {
  trigger: React.ReactNode;
  sections: ActionMenuItem[][];
  align?: 'start' | 'center' | 'end';
  side?: 'top' | 'bottom' | 'left' | 'right';
}

export default function ActionMenu({
  trigger,
  sections,
  align = 'end',
  side = 'top',
}: ActionMenuProps) {
  return (
    <DropdownMenu.Root>
      <DropdownMenu.Trigger asChild>{trigger}</DropdownMenu.Trigger>
      <DropdownMenu.Portal>
        <DropdownMenu.Content
          align={align}
          side={side}
          sideOffset={8}
          className="w-52 bg-surface rounded-xl shadow-xl border border-text/10 overflow-hidden z-50"
        >
          {sections.map((section, si) => (
            <React.Fragment key={si}>
              {si > 0 && (
                <DropdownMenu.Separator className="h-px bg-text/10 my-0" />
              )}
              {section.map((item, ii) => (
                <DropdownMenu.Item
                  key={ii}
                  onSelect={item.onClick}
                  disabled={item.disabled}
                  className={`px-4 py-3 flex items-center gap-3 text-sm font-medium outline-none cursor-pointer transition-colors select-none
                    data-[disabled]:opacity-50 data-[disabled]:cursor-not-allowed
                    data-[highlighted]:bg-background/60
                    ${item.destructive ? 'text-red-500' : 'text-text'}`}
                >
                  {item.icon && (
                    <span className="w-4 h-4 shrink-0 flex items-center justify-center">
                      {item.icon}
                    </span>
                  )}
                  {item.label}
                </DropdownMenu.Item>
              ))}
            </React.Fragment>
          ))}
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu.Root>
  );
}
