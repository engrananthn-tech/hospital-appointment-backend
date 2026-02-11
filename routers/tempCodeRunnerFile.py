@router.patch("/me", response_model= schemas.DoctorOwnerOutput)
# def activate(db: Session = Depends(get_db), current_user: dict = Depends(oauth2.get_current_user)):
#     query = db.query(models.Doctor).filter(models.Doctor.user_id == current_user.user_id)
#     current_doctor = query.first()
#     if not current_doctor:
#         raise HTTPException(status_code=404, detail="doctor not found")
#     if current_doctor.is_active:
#         raise HTTPException(status_code=409, detail="Profile is already active")
#     current_doctor.is_active = True
#     db.commit()
#     return query.first()