import os

# Configurar variables de entorno manualmente
os.environ['SUPABASE_URL'] = 'https://fbiikuhssfyrsckjtjbw.supabase.co'
os.environ['SUPABASE_ANON_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZiaWlrdWhzc2Z5cnNja2p0amJ3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MTY3NTU1MTYsImV4cCI6MjAzMjMzMTUxNn0.KGH1cWotbr-PaJ-yB0EiVZsY_I6_jRPZKJEDnSr8FMU'

print("✅ Variables de entorno de Supabase configuradas:")
print(f"  SUPABASE_URL: {os.environ.get('SUPABASE_URL')}")
print(f"  SUPABASE_ANON_KEY: {os.environ.get('SUPABASE_ANON_KEY')[:15]}...{os.environ.get('SUPABASE_ANON_KEY')[-5:]}")

# Verificar si las variables están configuradas
if os.environ.get('SUPABASE_URL') and os.environ.get('SUPABASE_ANON_KEY'):
    print("✅ Credenciales configuradas correctamente")
else:
    print("❌ Error: Credenciales no configuradas correctamente") 