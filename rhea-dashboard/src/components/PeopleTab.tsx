export default function PeopleTab() {
  return (
    <div className="space-y-3">
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
        <h3 className="font-medium text-sm mb-3">Collaborators</h3>
        <div className="space-y-2 text-xs">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-full bg-blue-500 flex items-center justify-center text-xs font-bold">S</div>
            <div>
              <p className="text-slate-300">You (Owner)</p>
              <p className="text-slate-500">Active now</p>
            </div>
          </div>
        </div>
      </div>
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
        <h3 className="font-medium text-sm mb-2">Invites</h3>
        <p className="text-xs text-slate-400">No pending invitations</p>
      </div>
    </div>
  )
}
