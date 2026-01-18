import { redirect } from 'next/navigation';

// STEP 1: Route `/` → `/documents` - Make Document Cards view the default entry screen
export default function Home() {
  redirect('/documents');
}
