/*****************************************************************************
  Copyright (c) 2011, Intel Corp.
  All rights reserved.

  Redistribution and use in source and binary forms, with or without
  modification, are permitted provided that the following conditions are met:

    * Redistributions of source code must retain the above copyright notice,
      this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * Neither the name of Intel Corporation nor the names of its contributors
      may be used to endorse or promote products derived from this software
      without specific prior written permission.

  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
  AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
  ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
  LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
  CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
  SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
  INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
  CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
  ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
  THE POSSIBILITY OF SUCH DAMAGE.
*****************************************************************************
* Contents: Native middle-level C interface to LAPACK function dlarfb
* Author: Intel Corporation
* Generated November, 2011
*****************************************************************************/

#include "lapacke.h"
#include "lapacke_utils.h"

lapack_int LAPACKE_dlarfb_work( int matrix_order, char side, char trans,
                                char direct, char storev, lapack_int m,
                                lapack_int n, lapack_int k, const double* v,
                                lapack_int ldv, const double* t, lapack_int ldt,
                                double* c, lapack_int ldc, double* work,
                                lapack_int ldwork )
{
    lapack_int info = 0;
    if( matrix_order == LAPACK_COL_MAJOR ) {
        /* Call LAPACK function and adjust info */
        LAPACK_dlarfb( &side, &trans, &direct, &storev, &m, &n, &k, v, &ldv, t,
                       &ldt, c, &ldc, work, &ldwork );
        if( info < 0 ) {
            info = info - 1;
        }
    } else if( matrix_order == LAPACK_ROW_MAJOR ) {
        lapack_int nrows_v = ( LAPACKE_lsame( storev, 'c' ) &&
                             LAPACKE_lsame( side, 'l' ) ) ? m :
                             ( ( LAPACKE_lsame( storev, 'c' ) &&
                             LAPACKE_lsame( side, 'r' ) ) ? n :
                             ( LAPACKE_lsame( storev, 'r' ) ? k : 1) );
        lapack_int ncols_v = LAPACKE_lsame( storev, 'c' ) ? k :
                             ( ( LAPACKE_lsame( storev, 'r' ) &&
                             LAPACKE_lsame( side, 'l' ) ) ? m :
                             ( ( LAPACKE_lsame( storev, 'r' ) &&
                             LAPACKE_lsame( side, 'r' ) ) ? n : 1) );
        lapack_int ldc_t = MAX(1,m);
        lapack_int ldt_t = MAX(1,k);
        lapack_int ldv_t = MAX(1,nrows_v);
        double* v_t = NULL;
        double* t_t = NULL;
        double* c_t = NULL;
        /* Check leading dimension(s) */
        if( ldc < n ) {
            info = -14;
            LAPACKE_xerbla( "LAPACKE_dlarfb_work", info );
            return info;
        }
        if( ldt < k ) {
            info = -12;
            LAPACKE_xerbla( "LAPACKE_dlarfb_work", info );
            return info;
        }
        if( ldv < ncols_v ) {
            info = -10;
            LAPACKE_xerbla( "LAPACKE_dlarfb_work", info );
            return info;
        }
        /* Allocate memory for temporary array(s) */
        v_t = (double*)
            LAPACKE_malloc( sizeof(double) * ldv_t * MAX(1,ncols_v) );
        if( v_t == NULL ) {
            info = LAPACK_TRANSPOSE_MEMORY_ERROR;
            goto exit_level_0;
        }
        t_t = (double*)LAPACKE_malloc( sizeof(double) * ldt_t * MAX(1,k) );
        if( t_t == NULL ) {
            info = LAPACK_TRANSPOSE_MEMORY_ERROR;
            goto exit_level_1;
        }
        c_t = (double*)LAPACKE_malloc( sizeof(double) * ldc_t * MAX(1,n) );
        if( c_t == NULL ) {
            info = LAPACK_TRANSPOSE_MEMORY_ERROR;
            goto exit_level_2;
        }
        /* Transpose input matrices */
        if( LAPACKE_lsame( storev, 'c' ) && LAPACKE_lsame( direct, 'f' ) ) {
            LAPACKE_dtr_trans( matrix_order, 'l', 'u', k, v, ldv, v_t, ldv_t );
            LAPACKE_dge_trans( matrix_order, nrows_v-k, ncols_v, &v[k*ldv], ldv,
                               &v_t[k], ldv_t );
        } else if( LAPACKE_lsame( storev, 'c' ) &&
                   LAPACKE_lsame( direct, 'b' ) ) {
            if( k > nrows_v ) {
                LAPACKE_xerbla( "LAPACKE_dlarfb_work", -8 );
                return -8;
            }
            LAPACKE_dtr_trans( matrix_order, 'u', 'u', k, &v[(nrows_v-k)*ldv],
                               ldv, &v_t[nrows_v-k], ldv_t );
            LAPACKE_dge_trans( matrix_order, nrows_v-k, ncols_v, v, ldv, v_t,
                               ldv_t );
        } else if( LAPACKE_lsame( storev, 'r' ) &&
                   LAPACKE_lsame( direct, 'f' ) ) {
            LAPACKE_dtr_trans( matrix_order, 'u', 'u', k, v, ldv, v_t, ldv_t );
            LAPACKE_dge_trans( matrix_order, nrows_v, ncols_v-k, &v[k], ldv,
                               &v_t[k*ldv_t], ldv_t );
        } else if( LAPACKE_lsame( storev, 'r' ) &&
                   LAPACKE_lsame( direct, 'f' ) ) {
            if( k > ncols_v ) {
                LAPACKE_xerbla( "LAPACKE_dlarfb_work", -8 );
                return -8;
            }
            LAPACKE_dtr_trans( matrix_order, 'l', 'u', k, &v[ncols_v-k], ldv,
                               &v_t[(ncols_v-k)*ldv_t], ldv_t );
            LAPACKE_dge_trans( matrix_order, nrows_v, ncols_v-k, v, ldv, v_t,
                               ldv_t );
        }
        LAPACKE_dge_trans( matrix_order, k, k, t, ldt, t_t, ldt_t );
        LAPACKE_dge_trans( matrix_order, m, n, c, ldc, c_t, ldc_t );
        /* Call LAPACK function and adjust info */
        LAPACK_dlarfb( &side, &trans, &direct, &storev, &m, &n, &k, v_t, &ldv_t,
                       t_t, &ldt_t, c_t, &ldc_t, work, &ldwork );
        info = 0;  /* LAPACK call is ok! */
        /* Transpose output matrices */
        LAPACKE_dge_trans( LAPACK_COL_MAJOR, m, n, c_t, ldc_t, c, ldc );
        /* Release memory and exit */
        LAPACKE_free( c_t );
exit_level_2:
        LAPACKE_free( t_t );
exit_level_1:
        LAPACKE_free( v_t );
exit_level_0:
        if( info == LAPACK_TRANSPOSE_MEMORY_ERROR ) {
            LAPACKE_xerbla( "LAPACKE_dlarfb_work", info );
        }
    } else {
        info = -1;
        LAPACKE_xerbla( "LAPACKE_dlarfb_work", info );
    }
    return info;
}
