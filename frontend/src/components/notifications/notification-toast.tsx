/**
 * SHUNYA — Notification Toast Stack
 *
 * Standalone toast overlay component. Can be rendered separately from
 * NotificationProvider when you need the toast view without the full context.
 *
 * The primary toast rendering lives inside notification-context.tsx's
 * NotificationProvider — this file re-exports a standalone version
 * for flexibility.
 */
export { NotificationToast } from './notification-toast-impl';

// Load the standalone toast implementation