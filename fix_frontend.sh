cd ~/tripsync
sed -i '' 's/route.total_estimated_cost_CAD || 2850/route.total_estimated_cost_CAD || "?"/g' index.html
sed -i '' 's/route.savings_vs_direct_percent || 42/route.savings_vs_direct_percent || "?"/g' index.html
echo "Frontend updated to show errors instead of hardcoded values"
