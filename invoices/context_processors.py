import os
def company(request):
 keys=['NAME','EMAIL','PHONE','ADDRESS','TAX_ID','BANK_NAME','BANK_ACCOUNT_NAME','BANK_ACCOUNT_NUMBER']
 data={k.lower():os.getenv('COMPANY_'+k,'') for k in keys}
 data['name']=data['name'] or 'Luztow Resources Ltd'
 return {'company':data}
