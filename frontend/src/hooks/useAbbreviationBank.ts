import { create } from 'zustand'

import type { AbbreviationBank } from '@/api/types/api.types'

interface AbbreviationBankStore {
  bank: AbbreviationBank
  isOpen: boolean
  setBank: (bank: AbbreviationBank) => void
  clearBank: () => void
  open: () => void
  close: () => void
}

export const useAbbreviationBankStore = create<AbbreviationBankStore>()((set) => ({
  bank: {},
  isOpen: false,
  setBank: (bank) => set({ bank }),
  clearBank: () => set({ bank: {}, isOpen: false }),
  open: () => set({ isOpen: true }),
  close: () => set({ isOpen: false }),
}))

export function useAbbreviationBank() {
  const { bank, isOpen, setBank, clearBank, open, close } = useAbbreviationBankStore()
  return { bank, isOpen, setBank, clearBank, open, close }
}