interface BottomNavProps {
  active: string
  onChange: (nav: string) => void
}

export default function BottomNav({ active, onChange }: BottomNavProps) {
  const navItems = [
    { id: 'ai', label: 'AI', icon: '🤖' },
    { id: 'people', label: 'People', icon: '👥' },
    { id: 'shield', label: 'Shield', icon: '🛡️' },
    { id: 'cart', label: 'Services', icon: '🛒' },
    { id: 'bio', label: 'BioRenderer', icon: '🧬' },
    { id: 'docs', label: 'Docs', icon: '📖' },
    { id: 'live', label: 'Live', icon: '🔴' },
  ]

  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-slate-800 border-t border-slate-700 px-2 py-2 flex justify-around">
      {navItems.map(item => (
        <button
          key={item.id}
          onClick={() => onChange(item.id)}
          className={`flex flex-col items-center gap-1 px-3 py-2 rounded text-xs transition ${
            active === item.id
              ? 'text-green-400'
              : 'text-slate-400 hover:text-slate-300'
          }`}
        >
          <span className="text-xl">{item.icon}</span>
          <span className="hidden sm:inline">{item.label}</span>
        </button>
      ))}
    </nav>
  )
}
