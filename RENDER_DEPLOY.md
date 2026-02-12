# Deploy Frontend on Render

## Steps:
1. Go to https://dashboard.render.com/
2. New + → Web Service
3. Connect GitHub repo: kittipond2365/tofubadminton
4. Settings:
   - Name: badminton-frontend
   - Root Directory: frontend
   - Runtime: Docker
   - Dockerfile Path: ./Dockerfile.prod
5. Environment Variables:
   - NEXT_PUBLIC_API_URL=https://badminton-backend.onrender.com/api/v1
   - NEXT_PUBLIC_WEB_PUSH_VAPID_PUBLIC_KEY=<your-key>
   - NODE_ENV=production
6. Click Create Web Service
7. Wait 3-5 minutes for deployment

## After Deploy:
- Update LINE Callback URL to new Render URL
- Test login flow
- Verify colors are showing (not grayscale)
