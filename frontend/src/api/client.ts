/** Shared API client. Preserve the PDF contract; keep a single error translation path. */
declare global { interface Window { __APP_CONFIG__?: { apiBaseUrl:string } } }
const BASE=window.__APP_CONFIG__?.apiBaseUrl??'/api';
export type AdmissionClass={id:string;name:string;totalSeats:number;heldSeats:number;confirmedSeats:number;availableSeats:number};
export type Hold={holdId:string;classId:string;className?:string;studentId?:string;status:string;expiresAt:string};
export const validStudent=(s:string)=>/^\d{17}$/.test(s);
export async function request<T>(method:string,path:string,studentId?:string,data?:unknown,adminKey?:string):Promise<T>{
  const headers:Record<string,string>={};
  if(studentId)headers['X-Student-Id']=studentId;
  if(adminKey)headers['X-Admin-Key']=adminKey;
  if(data!==undefined)headers['Content-Type']='application/json';
  let response:Response;
  try{response=await fetch(BASE+path,{method,headers,body:data===undefined?undefined:JSON.stringify(data),cache:'no-store',signal:AbortSignal.timeout(15000)});}
  catch{throw new Error(method==='GET'?'Cannot connect to the server. Refresh shortly.':'Request outcome unknown (timeout/network). Refresh My Applications before retrying to avoid duplicate submissions.');}
  if(!response.ok){
    const body:unknown=await response.json().catch(()=>({}));
    const error=body!==null&&typeof body==='object'&&'error' in body&&typeof body.error==='string'?body.error:`Request failed (${response.status})`;
    if(response.status===429)throw new Error('Too many requests. Please try again shortly.');
    if(response.status===503)throw new Error('Admission service is temporarily busy. Please retry.');
    throw new Error(error);
  }
  return response.status===204?undefined as T:await response.json() as T;
}
