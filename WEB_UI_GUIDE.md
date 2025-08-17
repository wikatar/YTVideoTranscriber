# Web UI Guide - Video Transcription System

## 🌐 **Modern Web Interface with shadcn/ui**

I've built a beautiful, modern web interface using **Next.js 14** and **shadcn/ui** that integrates directly with your existing backend functionality. No mocking - everything connects to your real transcription system!

## 🚀 **Quick Start**

### **Option 1: Start Everything (Recommended)**
```bash
# Starts both API server and Web UI
./start_full_system.sh

# Then open: http://localhost:3000
```

### **Option 2: Start Separately**
```bash
# Terminal 1: Start API server
python3 start_api.py

# Terminal 2: Start Web UI
./start_web_ui.sh
```

### **Option 3: Manual Start**
```bash
# Start API server
cd VideoTranscriptionmodel
python3 -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

# Start Web UI (in another terminal)
cd VideoTranscriptionmodel/web-ui
npm run dev
```

## 🎯 **Web UI Features**

### **📊 Dashboard Overview**
- **Real-time system status** - Running/stopped, processing stats
- **Storage optimization metrics** - Shows savings from immediate cleanup
- **Performance monitoring** - Processing times, videos per hour
- **System controls** - Start/stop monitoring, run cycles

### **📺 Channel Management**
- **Add channels easily** - Just paste YouTube URLs
- **Channel status tracking** - Active/inactive, last checked times
- **Supported URL formats** - @username, /c/, /channel/, /user/
- **Direct channel links** - Click to view on YouTube

### **🎬 Video Processing**
- **Process single videos** - Immediate processing of specific URLs
- **Video status tracking** - Pending, downloading, transcribing, completed
- **Transcription viewer** - View full transcripts with timestamps
- **Speaker identification** - See who said what and when

### **🔍 Search & Analytics**
- **Keyword search** - Search across all transcriptions
- **Relevance ranking** - Results sorted by match quality
- **Trending topics** - See what's popular across your content
- **Advanced filtering** - Date ranges, channels, confidence scores

### **💾 Storage Management**
- **Real-time usage monitoring** - See current storage usage
- **Optimization status** - Track immediate cleanup savings
- **File type breakdown** - Understand what's using space
- **Smart cleanup controls** - Normal and emergency cleanup options

## 🎨 **UI Components & Design**

### **Built with shadcn/ui**
- **Modern design system** - Clean, professional interface
- **Responsive layout** - Works on desktop, tablet, and mobile
- **Dark/light theme ready** - Built-in theme support
- **Accessible components** - WCAG compliant interface

### **Key UI Elements**
- **Status badges** - Color-coded system status indicators
- **Progress bars** - Real-time processing progress
- **Data tables** - Sortable, filterable video and channel lists
- **Modal dialogs** - Transcription viewer, confirmations
- **Toast notifications** - Success/error feedback
- **Loading states** - Smooth loading indicators

## 🔧 **Technical Architecture**

### **Frontend Stack**
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first styling
- **shadcn/ui** - High-quality component library
- **Tanstack Query** - Data fetching and caching
- **Lucide React** - Beautiful icons

### **Backend Integration**
- **FastAPI** - High-performance Python API
- **Real-time updates** - Auto-refreshing data every 30 seconds
- **Error handling** - Graceful error states and recovery
- **Type safety** - Full TypeScript types for API responses

### **API Endpoints**
```
GET  /status              - System status
GET  /channels            - List channels
POST /channels            - Add channel
GET  /videos              - List videos
GET  /videos/{id}/transcription - Get transcription
POST /videos/process      - Process video
POST /monitoring/start    - Start monitoring
POST /monitoring/stop     - Stop monitoring
POST /search              - Search videos
GET  /analytics/trending  - Trending topics
GET  /storage             - Storage status
POST /storage/cleanup     - Cleanup storage
```

## 📱 **Interface Screenshots**

### **Dashboard Overview**
- System status cards showing running state, channels, processed videos
- Storage optimization metrics with immediate cleanup savings
- Performance charts and processing statistics
- Control panel with start/stop monitoring buttons

### **Channel Management**
- Simple form to add YouTube channels with URL validation
- Table showing all monitored channels with status and last check times
- Direct links to view channels on YouTube
- Real-time status updates

### **Video Processing**
- Form to process individual videos immediately
- Tabbed interface showing all/pending/completed videos
- Detailed video information with duration, upload date, status
- Transcription viewer with timestamps and speaker identification

### **Search & Analytics**
- Keyword search with relevance scoring
- Trending topics dashboard with frequency and video counts
- Search results with matched keywords highlighted
- Export functionality for further analysis

### **Storage Management**
- Real-time storage usage with progress bars
- File type breakdown showing temporary vs permanent storage
- Optimization settings display
- Smart cleanup controls with confirmation dialogs

## 🎮 **Usage Examples**

### **Daily Workflow**
1. **Open Web UI**: Navigate to `http://localhost:3000`
2. **Check Status**: View system overview and current processing
3. **Add Channels**: Use the Channels tab to add new YouTube channels
4. **Monitor Progress**: Watch videos being discovered and processed
5. **Search Content**: Use Search tab to find specific topics
6. **Manage Storage**: Check Storage tab for optimization status

### **Adding Channels**
1. Go to **Channels** tab
2. Paste YouTube channel URL in the input field
3. Click **Add Channel**
4. Channel appears in the list with "Active" status
5. System automatically starts monitoring for new videos

### **Processing Videos**
1. Go to **Videos** tab
2. Enter YouTube video URL in "Process Single Video" section
3. Click **Process** - video starts processing immediately
4. Watch status change from "Pending" → "Downloading" → "Transcribing" → "Completed"
5. Click **Transcript** button to view full transcription

### **Searching Content**
1. Go to **Search & Analytics** tab
2. Enter keywords in search box (comma-separated)
3. View results ranked by relevance
4. Click **View** to see original video
5. Check **Trending Topics** for popular content themes

## ⚙️ **Configuration**

### **Environment Variables**
Create `web-ui/.env.local`:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### **API Configuration**
The FastAPI server automatically:
- Enables CORS for `http://localhost:3000`
- Provides OpenAPI docs at `http://localhost:8000/docs`
- Handles all existing backend functionality
- Supports real-time updates

## 🔍 **Development**

### **Project Structure**
```
web-ui/
├── src/
│   ├── app/                 # Next.js App Router
│   │   ├── layout.tsx       # Root layout with providers
│   │   └── page.tsx         # Main dashboard page
│   ├── components/
│   │   ├── ui/              # shadcn/ui components
│   │   ├── dashboard/       # Dashboard-specific components
│   │   └── providers/       # React Query provider
│   └── lib/
│       ├── api.ts           # API client and types
│       └── utils.ts         # Utility functions
├── package.json
└── tailwind.config.js
```

### **Adding New Features**
1. **Add API endpoint** in `src/api/main.py`
2. **Update API client** in `web-ui/src/lib/api.ts`
3. **Create UI component** in `web-ui/src/components/dashboard/`
4. **Add to main dashboard** in `web-ui/src/app/page.tsx`

## 🚨 **Troubleshooting**

### **Common Issues**

**API Connection Failed**
```bash
# Check if API server is running
curl http://localhost:8000/status

# Start API server
python3 start_api.py
```

**Web UI Won't Start**
```bash
# Install dependencies
cd web-ui && npm install

# Start development server
npm run dev
```

**CORS Errors**
- Make sure API server allows `http://localhost:3000`
- Check `NEXT_PUBLIC_API_URL` environment variable

**Missing Data**
- Ensure your existing database has data
- Run `python main.py status` to check CLI system
- Add some channels and process videos first

## 🎉 **What You Get**

### **Complete Integration**
- ✅ **No mocking** - Everything connects to your real backend
- ✅ **Real-time updates** - Live system status and progress
- ✅ **Full functionality** - All CLI features available in web UI
- ✅ **Modern design** - Professional, responsive interface

### **Enhanced Experience**
- ✅ **Visual feedback** - Progress bars, status indicators, notifications
- ✅ **Easy management** - Point-and-click channel and video management
- ✅ **Rich search** - Visual search results with relevance scoring
- ✅ **Storage insights** - Clear visualization of optimization benefits

### **Production Ready**
- ✅ **Type safety** - Full TypeScript coverage
- ✅ **Error handling** - Graceful error states and recovery
- ✅ **Performance** - Optimized queries and caching
- ✅ **Accessibility** - WCAG compliant components

**Your transcription system now has a beautiful, modern web interface that makes it incredibly easy to manage channels, monitor processing, and search your transcribed content!** 🚀
