import React, { useState } from 'react'
import ReactDOM from 'react-dom/client'
import { Button } from '@/components/ui/button'
import { Dialog, DialogTrigger, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogClose } from '@/components/ui/dialog'
import { Toaster, toast } from 'react-hot-toast'
import { QueryClient, QueryClientProvider, useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import './index.css'

const API_BASE = 'http://localhost:8000/api'

function App() {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('token'))
  const [pwdOpen, setPwdOpen] = useState(false)

  // login form state
  const [email, setEmail] = useState('admin@test.com')
  const [password, setPassword] = useState('123456')

  // change password state
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')

  // new user form state
  const [newUserEmail, setNewUserEmail] = useState('')
  const [newUserName, setNewUserName] = useState('')
  const [newUserPassword, setNewUserPassword] = useState('')

  const queryClient = useQueryClient()

  const meQuery = useQuery({
    queryKey: ['me', token],
    enabled: !!token,
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/auth/me`, { headers: { Authorization: `Bearer ${token}` } })
      if (!res.ok) throw new Error(`Failed to fetch me: ${res.status}`)
      return res.json()
    },
  })

  const isAdmin = meQuery.data?.email === 'admin@test.com'

  const usersQuery = useQuery({
    queryKey: ['users', token],
    enabled: !!token && !!isAdmin,
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/users`, { headers: { Authorization: `Bearer ${token}` } })
      if (!res.ok) throw new Error('Failed to fetch users')
      return res.json()
    },
  })

  const loginMutation = useMutation({
    mutationFn: async ({ email, password }: { email: string; password: string }) => {
      const formData = new URLSearchParams()
      formData.append('username', email)
      formData.append('password', password)
      const res = await fetch(`${API_BASE}/auth/token`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData,
      })
      if (!res.ok) throw new Error('Login failed')
      return res.json()
    },
    onSuccess: async (data) => {
      const t = data.access_token as string
      setToken(t)
      localStorage.setItem('token', t)
      await queryClient.invalidateQueries({ queryKey: ['me'] })
      toast.success('Logged in')
    },
    onError: (e: any) => {
      toast.error(e?.message || 'Login failed')
    },
  })

  const logout = async () => {
    try { await fetch(`${API_BASE}/auth/logout`, { method: 'POST' }) } catch {}
    setToken(null)
    localStorage.removeItem('token')
    queryClient.clear()
    toast.success('Logged out')
  }

  const changePasswordMutation = useMutation({
    mutationFn: async ({ current_password, new_password }: { current_password: string; new_password: string }) => {
      const res = await fetch(`${API_BASE}/auth/change-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ current_password, new_password }),
      })
      if (!res.ok) {
        const text = await res.text()
        throw new Error(text || 'Failed to change password')
      }
      return res.json()
    },
    onSuccess: () => {
      setCurrentPassword('')
      setNewPassword('')
      setPwdOpen(false)
      toast.success('Password changed')
    },
    onError: (e: any) => {
      toast.error(e?.message || 'Failed to change password')
    },
  })

  const createUserMutation = useMutation({
    mutationFn: async ({ email, name, password }: { email: string; name?: string; password: string }) => {
      const res = await fetch(`${API_BASE}/users`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ email, name, password }),
      })
      if (!res.ok) {
        const text = await res.text()
        throw new Error(text || 'Failed to create user')
      }
      return res.json()
    },
    onSuccess: async () => {
      setNewUserEmail('')
      setNewUserName('')
      setNewUserPassword('')
      await queryClient.invalidateQueries({ queryKey: ['users'] })
      toast.success('User created')
    },
    onError: (e: any) => toast.error(e?.message || 'Failed to create user'),
  })

  const deleteUserMutation = useMutation({
    mutationFn: async (id: string) => {
      const res = await fetch(`${API_BASE}/users/${id}`, { method: 'DELETE', headers: { Authorization: `Bearer ${token}` } })
      if (!res.ok) throw new Error('Failed to delete user')
      return res.json()
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['users'] })
      toast.success('User deleted')
    },
    onError: (e: any) => toast.error(e?.message || 'Failed to delete user'),
  })

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault()
    loginMutation.mutate({ email, password })
  }

  const handleChangePassword = (e: React.FormEvent) => {
    e.preventDefault()
    if (!token) return
    changePasswordMutation.mutate({ current_password: currentPassword, new_password: newPassword })
  }

  const handleCreateUser = (e: React.FormEvent) => {
    e.preventDefault()
    if (!token) return
    createUserMutation.mutate({ email: newUserEmail, name: newUserName, password: newUserPassword })
  }

  const handleDeleteUser = (id: string) => {
    if (!token) return
    deleteUserMutation.mutate(id)
  }

  return (
    <div className="min-h-screen p-8">
      <h1 className="text-2xl font-bold mb-8">Auth Demo</h1>

      {!token ? (
        <div className="min-h-screen flex items-center justify-center p-4 -m-8">
          <form onSubmit={handleLogin} className="space-y-3 p-6 border rounded w-full max-w-sm shadow bg-white">
          <h2 className="text-lg font-semibold">Login</h2>
          <div className="flex flex-col gap-1">
            <label className="text-sm">Email</label>
            <input className="border rounded px-3 py-2" value={email} onChange={e => setEmail(e.target.value)} />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-sm">Password</label>
            <input type="password" className="border rounded px-3 py-2" value={password} onChange={e => setPassword(e.target.value)} />
          </div>
          <Button type="submit" >Login</Button>
        </form>
        </div>
      ) : (
        <div className="max-w-3xl mx-auto space-y-6">
          <div className="flex items-center justify-between p-4 border rounded">
            <div>
              <div className="font-medium">Logged in as</div>
              <div>{meQuery.data?.email} {meQuery.data?.name ? `(${meQuery.data?.name})` : ''}</div>
            </div>
            <div className="flex items-center gap-2">
              <Dialog open={pwdOpen} onOpenChange={setPwdOpen}>
                
                <DialogTrigger asChild>
                  <Button variant="outline">Change Password</Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Change Password</DialogTitle>
                  </DialogHeader>
                  <form
                    onSubmit={handleChangePassword}
                    className="space-y-3"
                  >
                    <div className="flex flex-col gap-1">
                      <label className="text-sm">Current Password</label>
                      <input type="password" className="border rounded px-3 py-2 w-full" value={currentPassword} onChange={e => setCurrentPassword(e.target.value)} />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-sm">New Password</label>
                      <input type="password" className="border rounded px-3 py-2 w-full" value={newPassword} onChange={e => setNewPassword(e.target.value)} />
                    </div>
                    <DialogFooter>
                      <DialogClose asChild>
                        <Button type="button" variant="ghost">Cancel</Button>
                      </DialogClose>
                      <Button type="submit" disabled={changePasswordMutation.isPending || !currentPassword || !newPassword}>Save</Button>
                    </DialogFooter>
                  </form>
                </DialogContent>
              </Dialog>
              <Button onClick={logout} variant="secondary">Logout</Button>
            </div>
          </div>

          {isAdmin && (
            <div className="p-4 border rounded">
              <h2 className="text-lg font-semibold mb-3">User Management</h2>

              <form onSubmit={handleCreateUser} className="grid grid-cols-1 md:grid-cols-4 gap-2 mb-4">
                <input placeholder="Email" className="border rounded px-3 py-2" value={newUserEmail} onChange={e => setNewUserEmail(e.target.value)} />
                <input placeholder="Name (optional)" className="border rounded px-3 py-2" value={newUserName} onChange={e => setNewUserName(e.target.value)} />
                <input placeholder="Password" type="password" className="border rounded px-3 py-2" value={newUserPassword} onChange={e => setNewUserPassword(e.target.value)} />
                <Button type="submit" disabled={createUserMutation.isPending || !newUserEmail || !newUserPassword}>Create</Button>
              </form>

              <div className="space-y-2">
                {(usersQuery.data || []).map((u: any) => (
                  <div key={u.id} className="flex items-center justify-between border rounded px-3 py-2">
                    <div>
                      <div className="font-medium">{u.email}</div>
                      <div className="text-sm text-gray-600">{u.name || 'No name'}</div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button variant="destructive" onClick={() => handleDeleteUser(u.id)} disabled={u.email === 'admin@test.com'}>Delete</Button>
                    </div>
                  </div>
                ))}
                {(!usersQuery.data || usersQuery.data.length === 0) && <div className="text-sm text-gray-600">No users</div>}
              </div>
            </div>
          )}

          {!isAdmin && (
            <div className="p-4 border rounded text-sm text-gray-600">
              User Management is only available to admin.
            </div>
          )}
        </div>
      )}
    </div>
  )
}

const queryClient = new QueryClient()

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <Toaster position="top-right" />
      <App />
    </QueryClientProvider>
  </React.StrictMode>,
)
