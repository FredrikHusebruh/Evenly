import { Navigate, createBrowserRouter } from 'react-router'
import { Layout } from './components/Layout'
import { ProtectedRoute } from './auth/ProtectedRoute'
import { LoginPage } from './routes/LoginPage'
import { RegisterPage } from './routes/RegisterPage'
import { GroupsPage } from './routes/GroupsPage'
import { GroupDetailPage } from './routes/GroupDetailPage'
import { ReceiptCapturePage } from './routes/ReceiptCapturePage'
import { ReceiptReviewPage } from './routes/ReceiptReviewPage'
import { InvitePage } from './routes/InvitePage'

export const router = createBrowserRouter([
  { path: '/', element: <Navigate to="/groups" replace /> },
  { path: '/login', element: <LoginPage /> },
  { path: '/register', element: <RegisterPage /> },
  { path: '/invite/:code', element: <Layout><InvitePage /></Layout> },
  {
    path: '/groups',
    element: (
      <ProtectedRoute>
        <Layout>
          <GroupsPage />
        </Layout>
      </ProtectedRoute>
    ),
  },
  {
    path: '/groups/:groupId',
    element: (
      <ProtectedRoute>
        <Layout>
          <GroupDetailPage />
        </Layout>
      </ProtectedRoute>
    ),
  },
  {
    path: '/groups/:groupId/receipts/new',
    element: (
      <ProtectedRoute>
        <Layout>
          <ReceiptCapturePage />
        </Layout>
      </ProtectedRoute>
    ),
  },
  {
    path: '/groups/:groupId/receipts/:receiptId',
    element: (
      <ProtectedRoute>
        <Layout>
          <ReceiptReviewPage />
        </Layout>
      </ProtectedRoute>
    ),
  },
])
