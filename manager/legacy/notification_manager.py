import pandas as pd
import os
from datetime import datetime, timedelta
from pathlib import Path
import json

class NotificationManager:
    """Notification and alert management system"""
    
    def __init__(self):
        self.notifications_file = "data/notifications.csv"
        self.notification_settings_file = "data/notification_settings.json"
        self.init_data_files()
    
    def init_data_files(self):
        """Initialize data files if they don't exist"""
        Path("data").mkdir(exist_ok=True)
        
        # Initialize notifications file
        if not os.path.exists(self.notifications_file):
            df = pd.DataFrame(columns=[
                'notification_id', 'user_id', 'title', 'message', 'type',
                'priority', 'category', 'reference_id', 'reference_type',
                'is_read', 'is_dismissed', 'created_at', 'read_at'
            ])
            df.to_csv(self.notifications_file, index=False, encoding='utf-8-sig')
        
        # Initialize notification settings file
        if not os.path.exists(self.notification_settings_file):
            default_settings = {
                "email_notifications": True,
                "push_notifications": True,
                "low_stock_alerts": True,
                "overdue_invoice_alerts": True,
                "approval_request_alerts": True,
                "shipment_status_alerts": True,
                "payment_received_alerts": True,
                "system_maintenance_alerts": True,
                "daily_summary": True,
                "weekly_reports": False,
                "alert_thresholds": {
                    "low_stock_threshold": 10,
                    "overdue_days_threshold": 7,
                    "payment_reminder_days": 3
                }
            }
            
            with open(self.notification_settings_file, 'w', encoding='utf-8') as f:
                json.dump(default_settings, f, indent=2, ensure_ascii=False)
    
    def generate_notification_id(self):
        """Generate notification ID"""
        try:
            df = pd.read_csv(self.notifications_file, encoding='utf-8-sig')
            
            if df.empty:
                return "NOTIF0001"
            
            # Extract numbers from existing IDs
            existing_numbers = []
            for notif_id in df['notification_id']:
                if notif_id.startswith('NOTIF'):
                    try:
                        num = int(notif_id[5:])
                        existing_numbers.append(num)
                    except ValueError:
                        continue
            
            next_num = max(existing_numbers) + 1 if existing_numbers else 1
            return f"NOTIF{next_num:04d}"
        except Exception as e:
            print(f"Error generating notification ID: {e}")
            return f"NOTIF{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    def create_notification(self, user_id, title, message, notification_type="info",
                           priority="normal", category="general", reference_id=None,
                           reference_type=None):
        """Create new notification"""
        try:
            df = pd.read_csv(self.notifications_file, encoding='utf-8-sig')
            
            notification_id = self.generate_notification_id()
            
            notification_data = {
                'notification_id': notification_id,
                'user_id': user_id,
                'title': title,
                'message': message,
                'type': notification_type,
                'priority': priority,
                'category': category,
                'reference_id': reference_id,
                'reference_type': reference_type,
                'is_read': False,
                'is_dismissed': False,
                'created_at': datetime.now(),
                'read_at': None
            }
            
            new_notification = pd.DataFrame([notification_data])
            df = pd.concat([df, new_notification], ignore_index=True)
            df.to_csv(self.notifications_file, index=False, encoding='utf-8-sig')
            
            return notification_id
        except Exception as e:
            print(f"Error creating notification: {e}")
            return None
    
    def get_user_notifications(self, user_id, unread_only=False, limit=None):
        """Get notifications for specific user"""
        try:
            df = pd.read_csv(self.notifications_file, encoding='utf-8-sig')
            
            # Filter by user
            user_notifications = df[df['user_id'] == user_id]
            
            # Filter unread only if requested
            if unread_only:
                user_notifications = user_notifications[user_notifications['is_read'] == False]
            
            # Sort by creation date (newest first)
            user_notifications = user_notifications.sort_values('created_at', ascending=False)
            
            # Apply limit if specified
            if limit:
                user_notifications = user_notifications.head(limit)
            
            return user_notifications
        except Exception as e:
            print(f"Error getting user notifications: {e}")
            return pd.DataFrame()
    
    def mark_as_read(self, notification_id, user_id=None):
        """Mark notification as read"""
        try:
            df = pd.read_csv(self.notifications_file, encoding='utf-8-sig')
            
            # Build condition
            condition = df['notification_id'] == notification_id
            if user_id:
                condition = condition & (df['user_id'] == user_id)
            
            if not condition.any():
                return False
            
            df.loc[condition, 'is_read'] = True
            df.loc[condition, 'read_at'] = datetime.now()
            df.to_csv(self.notifications_file, index=False, encoding='utf-8-sig')
            
            return True
        except Exception as e:
            print(f"Error marking notification as read: {e}")
            return False
    
    def mark_as_dismissed(self, notification_id, user_id=None):
        """Mark notification as dismissed"""
        try:
            df = pd.read_csv(self.notifications_file, encoding='utf-8-sig')
            
            # Build condition
            condition = df['notification_id'] == notification_id
            if user_id:
                condition = condition & (df['user_id'] == user_id)
            
            if not condition.any():
                return False
            
            df.loc[condition, 'is_dismissed'] = True
            df.to_csv(self.notifications_file, index=False, encoding='utf-8-sig')
            
            return True
        except Exception as e:
            print(f"Error marking notification as dismissed: {e}")
            return False
    
    def get_unread_count(self, user_id):
        """Get count of unread notifications for user"""
        try:
            df = pd.read_csv(self.notifications_file, encoding='utf-8-sig')
            unread = df[(df['user_id'] == user_id) & (df['is_read'] == False)]
            return len(unread)
        except Exception as e:
            print(f"Error getting unread count: {e}")
            return 0
    
    def broadcast_notification(self, title, message, notification_type="info",
                              priority="normal", category="system", exclude_users=None):
        """Broadcast notification to all users"""
        try:
            # Get all users from auth manager
            from auth_manager import AuthManager
            auth_manager = AuthManager()
            all_users = auth_manager.get_all_users()
            
            exclude_users = exclude_users or []
            created_notifications = []
            
            for _, user in all_users.iterrows():
                user_id = user['user_id']
                if user_id not in exclude_users:
                    notif_id = self.create_notification(
                        user_id, title, message, notification_type, 
                        priority, category
                    )
                    if notif_id:
                        created_notifications.append(notif_id)
            
            return created_notifications
        except Exception as e:
            print(f"Error broadcasting notification: {e}")
            return []
    
    def create_system_alerts(self):
        """Create system-generated alerts"""
        try:
            alerts_created = []
            
            # Low stock alerts
            if self.get_notification_setting('low_stock_alerts'):
                alerts_created.extend(self._create_low_stock_alerts())
            
            # Overdue invoice alerts
            if self.get_notification_setting('overdue_invoice_alerts'):
                alerts_created.extend(self._create_overdue_invoice_alerts())
            
            # Overdue shipment alerts
            if self.get_notification_setting('shipment_status_alerts'):
                alerts_created.extend(self._create_overdue_shipment_alerts())
            
            # Approval request alerts
            if self.get_notification_setting('approval_request_alerts'):
                alerts_created.extend(self._create_approval_request_alerts())
            
            return alerts_created
        except Exception as e:
            print(f"Error creating system alerts: {e}")
            return []
    
    def _create_low_stock_alerts(self):
        """Create low stock alerts"""
        try:
            from inventory_manager import InventoryManager
            inventory_manager = InventoryManager()
            
            low_stock_items = inventory_manager.get_low_stock_items()
            alerts_created = []
            
            for _, item in low_stock_items.iterrows():
                # Create alert for master users
                alert_id = self.create_notification(
                    "master",
                    "Low Stock Alert",
                    f"Low stock: {item['product_name']} ({item['current_stock']} remaining)",
                    "warning",
                    "high",
                    "inventory",
                    item['product_id'],
                    "product"
                )
                if alert_id:
                    alerts_created.append(alert_id)
            
            return alerts_created
        except Exception as e:
            print(f"Error creating low stock alerts: {e}")
            return []
    
    def _create_overdue_invoice_alerts(self):
        """Create overdue invoice alerts"""
        try:
            from invoice_manager import InvoiceManager
            invoice_manager = InvoiceManager()
            
            overdue_invoices = invoice_manager.get_overdue_invoices()
            alerts_created = []
            
            for _, invoice in overdue_invoices.iterrows():
                alert_id = self.create_notification(
                    "master",
                    "Overdue Invoice Alert",
                    f"Invoice {invoice['invoice_number']} is overdue for {invoice['customer_name']}",
                    "error",
                    "high",
                    "finance",
                    invoice['invoice_id'],
                    "invoice"
                )
                if alert_id:
                    alerts_created.append(alert_id)
            
            return alerts_created
        except Exception as e:
            print(f"Error creating overdue invoice alerts: {e}")
            return []
    
    def _create_overdue_shipment_alerts(self):
        """Create overdue shipment alerts"""
        try:
            from shipping_manager import ShippingManager
            shipping_manager = ShippingManager()
            
            overdue_shipments = shipping_manager.get_overdue_shipments()
            alerts_created = []
            
            for _, shipment in overdue_shipments.iterrows():
                alert_id = self.create_notification(
                    "master",
                    "Overdue Shipment Alert",
                    f"Shipment {shipment['shipment_number']} is overdue for {shipment['customer_name']}",
                    "warning",
                    "high",
                    "shipping",
                    shipment['shipment_id'],
                    "shipment"
                )
                if alert_id:
                    alerts_created.append(alert_id)
            
            return alerts_created
        except Exception as e:
            print(f"Error creating overdue shipment alerts: {e}")
            return []
    
    def _create_approval_request_alerts(self):
        """Create approval request alerts"""
        try:
            from approval_manager import ApprovalManager
            approval_manager = ApprovalManager()
            
            pending_requests = approval_manager.get_pending_requests()
            alerts_created = []
            
            for _, request in pending_requests.iterrows():
                alert_id = self.create_notification(
                    "master",
                    "Approval Request",
                    f"New {request['request_type']} approval request from {request['requester_name']}",
                    "info",
                    "normal",
                    "approval",
                    request['request_id'],
                    "approval_request"
                )
                if alert_id:
                    alerts_created.append(alert_id)
            
            return alerts_created
        except Exception as e:
            print(f"Error creating approval request alerts: {e}")
            return []
    
    def get_notification_settings(self):
        """Get notification settings"""
        try:
            with open(self.notification_settings_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error getting notification settings: {e}")
            return {}
    
    def get_notification_setting(self, setting_key):
        """Get specific notification setting"""
        try:
            settings = self.get_notification_settings()
            return settings.get(setting_key, False)
        except Exception as e:
            print(f"Error getting notification setting: {e}")
            return False
    
    def update_notification_settings(self, settings):
        """Update notification settings"""
        try:
            with open(self.notification_settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error updating notification settings: {e}")
            return False
    
    def delete_old_notifications(self, days_old=30):
        """Delete old notifications"""
        try:
            df = pd.read_csv(self.notifications_file, encoding='utf-8-sig')
            
            # Convert created_at to datetime
            df['created_at'] = pd.to_datetime(df['created_at'])
            
            # Calculate cutoff date
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            # Keep notifications newer than cutoff date
            df_filtered = df[df['created_at'] > cutoff_date]
            
            # Save filtered data
            df_filtered.to_csv(self.notifications_file, index=False, encoding='utf-8-sig')
            
            return len(df) - len(df_filtered)  # Return number of deleted notifications
        except Exception as e:
            print(f"Error deleting old notifications: {e}")
            return 0
    
    def get_notification_statistics(self):
        """Get notification statistics"""
        try:
            df = pd.read_csv(self.notifications_file, encoding='utf-8-sig')
            
            stats = {
                'total_notifications': len(df),
                'unread_notifications': len(df[df['is_read'] == False]),
                'by_type': df['type'].value_counts().to_dict(),
                'by_priority': df['priority'].value_counts().to_dict(),
                'by_category': df['category'].value_counts().to_dict(),
                'dismissed_notifications': len(df[df['is_dismissed'] == True])
            }
            
            return stats
        except Exception as e:
            print(f"Error getting notification statistics: {e}")
            return {}
