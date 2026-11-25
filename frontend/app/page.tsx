import { redirect } from 'next/navigation'

// There is no landing page yet, so send visitors straight to sign-in.
export default function Home() {
  redirect('/login')
}
