#include <stdio.h>
#include <stdlib.h>
#define MAXLENGTH 10
#define INF 0x3f3f3f3f
void MERGE(int A[], int p, int q, int r);
void MERGE_SORT(int A[], int p, int r);

int main(int argc, char *argv[]){
	int start = 0;
	int end = 0;
	int i = 0;
	int NUM[MAXLENGTH] = {0};
	start = 0;
	end = 9;
	for(i=start; i<=end; i++){
		NUM[i]=9-i;
	}
	for (i = start; i <= end; i++){
		printf("%d ", NUM[i]);
	}
	printf("\n");
	MERGE_SORT(NUM, start, end);
	for (i = start; i <= end; i++){
		printf("%d ", NUM[i]);
	}
	return 0;
}

void MERGE_SORT(int A[], int p, int r){
	int q = 0;
	if(p<r){
		q = (p+r)/2;
		MERGE_SORT(A, p, q);
		MERGE_SORT(A, q+1, r);
		MERGE(A, p, q, r);
	}
}

void MERGE(int A[], int p, int q, int r){
	int n1 = 0;
	int n2 = 0;
	int i = 0;
	int L[MAXLENGTH] = {0};
	int j = 0;
	int R[MAXLENGTH] = {0};
	int k = 0;
	n1 = q-p+1;
	n2 = r-q;
	for(i=1; i<=n1; i++){
		L[i]=A[p+i-1];
	}
	for(j=1; j<=n2; j++){
		R[j]=A[q+j];
	}
	L[n1+1]=INF;
	R[n2+1]=INF;
	i = 1;
	j = 1;
	for(k=p; k<=r; k++){
		if(L[i]<=R[j]){
			A[k]=L[i];
			i++;
			}else{
			A[k]=R[j];
			j++;
		}
	}
}


